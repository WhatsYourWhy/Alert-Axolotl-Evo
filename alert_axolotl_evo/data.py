"""Data loading and generation."""

import csv
import json
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple


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
    """Load data from CSV file."""
    
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
        """Load data from CSV."""
        values = []
        anomalies = []
        
        with open(self.path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    value = float(row[self.value_column])
                    values.append(value)
                    
                    if self.anomaly_column and self.anomaly_column in row:
                        anomalies.append(row[self.anomaly_column].lower() in ("true", "1", "yes", "anomaly"))
                    else:
                        anomalies.append(False)
                except (ValueError, KeyError):
                    continue
        
        return values, anomalies


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
                self.anomaly_key,
            )
        else:
            raise ValueError(f"Unsupported file format: {self.path.suffix}")
        
        return loader.load()

