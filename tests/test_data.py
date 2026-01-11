"""Tests for data loading."""

import csv
import json
import tempfile
from pathlib import Path

import pytest

from alert_axolotl_evo.data import (
    CSVDataLoader,
    JSONDataLoader,
    MockDataLoader,
    create_data_loader,
)
from alert_axolotl_evo.config import Config, DataConfig


def test_mock_data_loader():
    """Test mock data loader."""
    loader = MockDataLoader(seed=42, size=10, anomaly_count=2, anomaly_multiplier=2.0)
    values, anomalies = loader.load()
    
    assert len(values) == 10
    assert len(anomalies) == 10
    assert sum(anomalies) == 2
    assert all(isinstance(v, float) for v in values)
    assert all(isinstance(a, bool) for a in anomalies)


def test_csv_data_loader():
    """Test CSV data loader."""
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["value", "timestamp", "is_anomaly"])
        writer.writeheader()
        writer.writerow({"value": "50.0", "timestamp": "2024-01-01", "is_anomaly": "False"})
        writer.writerow({"value": "120.0", "timestamp": "2024-01-02", "is_anomaly": "True"})
        writer.writerow({"value": "45.0", "timestamp": "2024-01-03", "is_anomaly": "False"})
        csv_file = Path(f.name)
    
    try:
        loader = CSVDataLoader(
            csv_file,
            value_column="value",
            timestamp_column="timestamp",
            anomaly_column="is_anomaly",
        )
        values, anomalies = loader.load()
        
        assert len(values) == 3
        assert len(anomalies) == 3
        assert values[0] == 50.0
        assert values[1] == 120.0
        assert anomalies[1] is True
        assert anomalies[0] is False
    finally:
        csv_file.unlink()


def test_json_data_loader():
    """Test JSON data loader."""
    # Create temporary JSON file
    data = [
        {"value": 50.0, "timestamp": "2024-01-01", "is_anomaly": False},
        {"value": 120.0, "timestamp": "2024-01-02", "is_anomaly": True},
        {"value": 45.0, "timestamp": "2024-01-03", "is_anomaly": False},
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        json_file = Path(f.name)
    
    try:
        loader = JSONDataLoader(
            json_file,
            value_key="value",
            timestamp_key="timestamp",
            anomaly_key="is_anomaly",
        )
        values, anomalies = loader.load()
        
        assert len(values) == 3
        assert len(anomalies) == 3
        assert values[0] == 50.0
        assert values[1] == 120.0
        assert anomalies[1] is True
        assert anomalies[0] is False
    finally:
        json_file.unlink()


def test_create_data_loader_mock():
    """Test create_data_loader with mock config."""
    config = DataConfig(data_source="mock", mock_size=20, anomaly_count=3)
    loader = create_data_loader(config)
    
    assert isinstance(loader, MockDataLoader)
    assert loader.size == 20
    assert loader.anomaly_count == 3


def test_create_data_loader_csv():
    """Test create_data_loader with CSV config."""
    # Create temporary CSV file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["value"])
        writer.writeheader()
        writer.writerow({"value": "50.0"})
        csv_file = Path(f.name)
    
    try:
        config = DataConfig(
            data_source="csv",
            data_path=csv_file,
            value_column="value",
        )
        loader = create_data_loader(config)
        
        assert isinstance(loader, CSVDataLoader)
        values, anomalies = loader.load()
        assert len(values) == 1
    finally:
        csv_file.unlink()


def test_create_data_loader_json():
    """Test create_data_loader with JSON config."""
    # Create temporary JSON file
    data = [{"value": 50.0}]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        json_file = Path(f.name)
    
    try:
        config = DataConfig(
            data_source="json",
            data_path=json_file,
            value_column="value",
        )
        loader = create_data_loader(config)
        
        assert isinstance(loader, JSONDataLoader)
        values, anomalies = loader.load()
        assert len(values) == 1
    finally:
        json_file.unlink()


def test_create_data_loader_missing_path():
    """Test create_data_loader with missing path for file-based sources."""
    config = DataConfig(data_source="csv", data_path=None)
    
    with pytest.raises(ValueError, match="data_path must be specified"):
        create_data_loader(config)

