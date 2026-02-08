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


def test_data_consistency_across_generations():
    """Test that consistent_data=True produces same data across generations."""
    loader = MockDataLoader(seed=42, size=100, anomaly_count=10, use_realistic_patterns=False)
    
    # Load data with same seed (simulating consistent_data=True)
    loader.seed = 42
    values1, anomalies1 = loader.load()
    
    loader.seed = 42  # Same seed, should produce same data
    values2, anomalies2 = loader.load()
    
    # Data should be identical
    assert values1 == values2
    assert anomalies1 == anomalies2
    assert len(values1) == 100
    assert sum(anomalies1) == 10


def test_data_variation_per_generation():
    """Test that consistent_data=False produces different data per generation."""
    loader = MockDataLoader(seed=42, size=100, anomaly_count=10, use_realistic_patterns=False)
    
    # Load data with seed + 0 (generation 0)
    loader.seed = 42
    values_gen0, anomalies_gen0 = loader.load()
    
    # Load data with seed + 1 (generation 1)
    loader.seed = 43
    values_gen1, anomalies_gen1 = loader.load()
    
    # Data should be different
    assert values_gen0 != values_gen1
    assert anomalies_gen0 != anomalies_gen1
    # But structure should be same
    assert len(values_gen0) == len(values_gen1) == 100
    assert sum(anomalies_gen0) == sum(anomalies_gen1) == 10


def test_seed_handling():
    """Test seed handling in both consistent and varying modes."""
    loader = MockDataLoader(seed=42, size=50, anomaly_count=5, use_realistic_patterns=False)
    
    # Test consistent mode (same seed)
    loader.seed = 100
    values1, _ = loader.load()
    loader.seed = 100
    values2, _ = loader.load()
    assert values1 == values2
    
    # Test varying mode (different seeds)
    loader.seed = 100
    values3, _ = loader.load()
    loader.seed = 101
    values4, _ = loader.load()
    assert values3 != values4


def test_realistic_data_anomaly_count():
    """Test that realistic data generation produces exact or near-exact anomaly count."""
    for size in [50, 100, 200, 500]:
        for anomaly_count in [5, 10, 25]:
            loader = MockDataLoader(
                seed=42,
                size=size,
                anomaly_count=anomaly_count,
                use_realistic_patterns=True
            )
            values, anomalies = loader.load()
            
            assert len(values) == size
            assert len(anomalies) == size
            actual_count = sum(anomalies)
            # Allow small variance due to spacing constraints with multi-point anomalies
            # Should be within 1-2 of target for reasonable cases
            assert actual_count >= anomaly_count - 2, f"Expected at least {anomaly_count - 2} anomalies, got {actual_count}"
            assert actual_count <= anomaly_count, f"Expected at most {anomaly_count} anomalies, got {actual_count}"


def test_realistic_data_deterministic():
    """Test that realistic data generation is deterministic with same seed."""
    loader1 = MockDataLoader(seed=42, size=100, anomaly_count=10, use_realistic_patterns=True)
    loader2 = MockDataLoader(seed=42, size=100, anomaly_count=10, use_realistic_patterns=True)
    
    values1, anomalies1 = loader1.load()
    values2, anomalies2 = loader2.load()
    
    # Same seed should produce same data
    assert values1 == values2
    assert anomalies1 == anomalies2


def test_realistic_data_patterns():
    """Test that realistic data includes various anomaly patterns."""
    loader = MockDataLoader(
        seed=42,
        size=200,
        anomaly_count=20,
        use_realistic_patterns=True
    )
    values, anomalies = loader.load()
    
    # Check that we have anomalies (allow small variance due to spacing)
    actual_count = sum(anomalies)
    assert actual_count >= 18, f"Expected at least 18 anomalies, got {actual_count}"
    assert actual_count <= 20, f"Expected at most 20 anomalies, got {actual_count}"
    
    # Check that anomalies have higher values (on average)
    anomaly_values = [v for v, a in zip(values, anomalies) if a]
    normal_values = [v for v, a in zip(values, anomalies) if not a]
    
    # Allow small variance due to spacing constraints
    assert len(anomaly_values) >= 18
    assert len(anomaly_values) <= 20
    assert len(normal_values) >= 180
    assert len(normal_values) <= 182
    
    # Anomalies should generally be higher (but not always due to trends/noise)
    avg_anomaly = sum(anomaly_values) / len(anomaly_values)
    avg_normal = sum(normal_values) / len(normal_values)
    # With multiplier 1.8 default, anomalies should be noticeably higher
    assert avg_anomaly > avg_normal * 1.2  # At least 20% higher on average


def test_realistic_data_trends():
    """Test that realistic data includes trends."""
    loader = MockDataLoader(
        seed=42,
        size=100,
        anomaly_count=5,
        use_realistic_patterns=True,
        trend_strength=0.2  # Stronger trend for testing
    )
    values, _ = loader.load()
    
    # Check that there's some variation (trend should create gradual change)
    # Split into thirds and check for trend
    third = len(values) // 3
    first_third_avg = sum(values[:third]) / third
    last_third_avg = sum(values[-third:]) / third
    
    # With trend_strength=0.2, there should be noticeable difference
    # (trend can go up or down, so check absolute difference)
    trend_magnitude = abs(last_third_avg - first_third_avg)
    assert trend_magnitude > 1.0  # Should have some trend effect


def test_realistic_data_edge_cases():
    """Test realistic data generation with edge cases."""
    # Small dataset
    loader = MockDataLoader(seed=42, size=10, anomaly_count=1, use_realistic_patterns=True)
    values, anomalies = loader.load()
    assert len(values) == 10
    assert sum(anomalies) == 1
    
    # Many anomalies (50% of data)
    loader = MockDataLoader(seed=42, size=100, anomaly_count=50, use_realistic_patterns=True)
    values, anomalies = loader.load()
    assert len(values) == 100
    assert sum(anomalies) == 50
    
    # Single anomaly
    loader = MockDataLoader(seed=42, size=100, anomaly_count=1, use_realistic_patterns=True)
    values, anomalies = loader.load()
    assert sum(anomalies) == 1
    
    # All values could be anomalies (edge case)
    loader = MockDataLoader(seed=42, size=5, anomaly_count=5, use_realistic_patterns=True)
    values, anomalies = loader.load()
    assert sum(anomalies) == 5