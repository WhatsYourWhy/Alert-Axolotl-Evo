"""Data loading and generation."""

import csv
import json
import logging
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DataLoader(ABC):
    """Abstract base class for data loaders."""
    
    @abstractmethod
    def load(self) -> Tuple[List[float], List[bool]]:
        """
        Load data and return (values, anomalies).
        
        Returns:
            Tuple of (values list, anomalies list) where anomalies is boolean list
            indicating which indices are anomalies.
        """
        pass


class MockDataLoader(DataLoader):
    """Generate deterministic mock latency data with anomalies."""
    
    def __init__(
        self,
        seed: int = 42,
        size: int = 100,
        anomaly_count: int = 8,
        anomaly_multiplier: float = 2.5,
    ):
        self.seed = seed
        self.size = size
        self.anomaly_count = anomaly_count
        self.anomaly_multiplier = anomaly_multiplier
    
    def load(self) -> Tuple[List[float], List[bool]]:
        """Generate mock data."""
        rng = random.Random(self.seed)
        values = [rng.gauss(50, 10) for _ in range(self.size)]
        anomaly_idx = set(rng.sample(range(self.size), self.anomaly_count))
        anomalies = []
        for idx, value in enumerate(values):
            if idx in anomaly_idx:
                values[idx] = value * self.anomaly_multiplier
                anomalies.append(True)
            else:
                anomalies.append(False)
        return values, anomalies


class CSVDataLoader(DataLoader):
    """Load data from CSV file with optional auto-labeling."""
    
    def __init__(
        self,
        path: Path,
        value_column: str = "value",
        timestamp_column: str = "timestamp",
        anomaly_column: Optional[str] = None,
        auto_label_percentile: float = 0.98,
    ):
        """
        Args:
            path: Path to CSV file
            value_column: Column name for numeric values
            timestamp_column: Column name for timestamps (optional, not used in load)
            anomaly_column: Column name for anomaly labels (optional)
                - If None: Explicitly means "no labels provided; auto-label if percentile is set"
                - If specified but missing in file: Treated as missing column (auto-labeling will occur)
            auto_label_percentile: Percentile threshold for auto-labeling when anomaly_column is missing
                                  Values above this percentile are labeled as anomalies
        """
        self.path = Path(path)
        self.value_column = value_column
        self.timestamp_column = timestamp_column
        self.anomaly_column = anomaly_column
        self.auto_label_percentile = auto_label_percentile
        # Provenance metadata for label source tracking
        self._label_source: Optional[str] = None  # "auto_percentile", "explicit", or None
        self._label_threshold: Optional[float] = None  # Threshold used for auto-labeling
    
    def load(self) -> Tuple[List[float], List[bool]]:
        """
        Load data from CSV.
        
        If anomaly_column is missing, auto-labels anomalies using percentile threshold.
        """
        values = []
        raw_values = []
        anomalies = []
        has_anomaly_column = False
        
        # First pass: load values and check for anomaly column
        with open(self.path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    value = float(row[self.value_column])
                    raw_values.append(value)
                    values.append(value)
                    
                    # Check if anomaly column exists in this row
                    if self.anomaly_column and self.anomaly_column in row:
                        has_anomaly_column = True
                        anomalies.append(
                            row[self.anomaly_column].lower() in ("true", "1", "yes", "anomaly")
                        )
                    else:
                        anomalies.append(None)  # Placeholder - will be auto-labeled if needed
                except (ValueError, KeyError):
                    continue
        
        # Auto-label if anomaly column was missing
        if not has_anomaly_column and raw_values:
            try:
                import numpy as np
                threshold = np.quantile(raw_values, self.auto_label_percentile)
                anomalies = [v > threshold for v in raw_values]
                
                # Set provenance metadata
                self._label_source = "auto_percentile"
                self._label_threshold = float(threshold)
                
                logger.warning(
                    "CSVDataLoader: anomaly column '%s' missing — auto-labeling top %.2f%% (threshold=%.2f)",
                    self.anomaly_column or "<not specified>",
                    (1 - self.auto_label_percentile) * 100,
                    threshold
                )
            except ImportError:
                # Fallback if numpy not available: use simple percentile calculation
                sorted_values = sorted(raw_values)
                threshold_idx = int(len(sorted_values) * self.auto_label_percentile)
                threshold = sorted_values[min(threshold_idx, len(sorted_values) - 1)]
                anomalies = [v > threshold for v in raw_values]
                
                # Set provenance metadata
                self._label_source = "auto_percentile"
                self._label_threshold = float(threshold)
                
                logger.warning(
                    "CSVDataLoader: anomaly column '%s' missing — auto-labeling top %.2f%% (threshold=%.2f, numpy not available)",
                    self.anomaly_column or "<not specified>",
                    (1 - self.auto_label_percentile) * 100,
                    threshold
                )
        elif has_anomaly_column:
            # Labels were explicitly provided
            self._label_source = "explicit"
            self._label_threshold = None
        
        return values, anomalies
    
    def get_label_provenance(self) -> dict:
        """
        Get provenance metadata about label source.
        
        Returns:
            Dict with keys:
            - label_source: "auto_percentile", "explicit", or None
            - label_threshold: Threshold used for auto-labeling (if applicable)
        """
        return {
            "label_source": self._label_source,
            "label_threshold": self._label_threshold,
        }


class JSONDataLoader(DataLoader):
    """Load data from JSON file."""
    
    def __init__(
        self,
        path: Path,
        value_key: str = "value",
        timestamp_key: str = "timestamp",
        anomaly_key: str = None,
    ):
        self.path = Path(path)
        self.value_key = value_key
        self.timestamp_key = timestamp_key
        self.anomaly_key = anomaly_key
    
    def load(self) -> Tuple[List[float], List[bool]]:
        """Load data from JSON."""
        values = []
        anomalies = []
        
        with open(self.path, "r") as f:
            data = json.load(f)
        
        # Handle array of objects
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    try:
                        value = float(item[self.value_key])
                        values.append(value)
                        
                        if self.anomaly_key and self.anomaly_key in item:
                            anomalies.append(
                                item[self.anomaly_key] is True
                                or str(item[self.anomaly_key]).lower() in ("true", "1", "yes", "anomaly")
                            )
                        else:
                            anomalies.append(False)
                    except (ValueError, KeyError):
                        continue
        # Handle object with arrays
        elif isinstance(data, dict):
            if self.value_key in data and isinstance(data[self.value_key], list):
                values = [float(v) for v in data[self.value_key]]
                if self.anomaly_key and self.anomaly_key in data:
                    anomalies = [
                        bool(a) or str(a).lower() in ("true", "1", "yes", "anomaly")
                        for a in data[self.anomaly_key]
                    ]
                else:
                    anomalies = [False] * len(values)
        
        return values, anomalies


class TimeSeriesDataLoader(DataLoader):
    """Load time-series data (wrapper around CSV/JSON with time handling)."""
    
    def __init__(
        self,
        path: Path,
        value_column: str = "value",
        timestamp_column: str = "timestamp",
        anomaly_column: str = None,
    ):
        self.path = Path(path)
        self.value_column = value_column
        self.timestamp_column = timestamp_column
        self.anomaly_column = anomaly_column
    
    def load(self) -> Tuple[List[float], List[bool]]:
        """Load time-series data."""
        if self.path.suffix == ".csv":
            loader = CSVDataLoader(
                self.path,
                self.value_column,
                self.timestamp_column,
                self.anomaly_column,
            )
        elif self.path.suffix == ".json":
            loader = JSONDataLoader(
                self.path,
                self.value_column,
                self.timestamp_column,
                self.anomaly_column,
            )
        else:
            raise ValueError(f"Unsupported file format: {self.path.suffix}")
        
        return loader.load()


def create_data_loader(config) -> DataLoader:
    """
    Create a DataLoader from config.
    
    Args:
        config: DataConfig instance
        
    Returns:
        DataLoader instance
    """
    if config.data_source == "mock":
        return MockDataLoader(
            seed=42,  # Will be overridden per generation
            size=config.mock_size,
            anomaly_count=config.anomaly_count,
            anomaly_multiplier=config.anomaly_multiplier,
        )
    elif config.data_source == "csv":
        if not config.data_path:
            raise ValueError("data_path must be specified for CSV data source")
        return CSVDataLoader(
            config.data_path,
            config.value_column,
            config.timestamp_column,
            config.anomaly_column,
        )
    elif config.data_source == "json":
        if not config.data_path:
            raise ValueError("data_path must be specified for JSON data source")
        return JSONDataLoader(
            config.data_path,
            config.value_column,
            config.timestamp_column,
            config.anomaly_column,
        )
    else:
        raise ValueError(f"Unknown data source: {config.data_source}")

