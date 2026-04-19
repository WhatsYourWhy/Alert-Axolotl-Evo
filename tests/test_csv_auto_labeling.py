"""
Test: Agnostic CSV Ingestion with Auto-Labeling.
Verifies the engine can synthesize ground truth from raw data.
"""
import csv
import tempfile
from pathlib import Path

from alert_axolotl_evo.data import CSVDataLoader


def test_csv_auto_labeling():
    """Test CSVDataLoader auto-labels anomalies when column is missing."""
    # Create temporary CSV file with spikes (no anomaly column)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "cpu_load"])
        writer.writeheader()
        
        # Generate normal data with 3 spikes
        for i in range(100):
            if i == 10:
                cpu_load = 150.0  # Spike 1
            elif i == 50:
                cpu_load = 145.0  # Spike 2
            elif i == 90:
                cpu_load = 160.0  # Spike 3
            else:
                cpu_load = 50.0 + (i % 10)  # Normal variation
            
            writer.writerow({
                "timestamp": f"2024-01-01T00:{i:02d}:00",
                "cpu_load": cpu_load
            })
        
        csv_file = Path(f.name)
    
    try:
        # Load WITHOUT specifying anomaly column (should auto-label)
        loader = CSVDataLoader(
            path=csv_file,
            value_column="cpu_load",
            anomaly_column="is_anomaly",  # Column doesn't exist in file
            auto_label_percentile=0.95,   # Top 5% should be flagged
        )
        
        values, anomalies = loader.load()
        
        # Verify interface integrity
        assert len(values) == len(anomalies), "Values and anomalies must have same length"
        assert len(values) == 100, "Should load all 100 rows"
        
        # Verify auto-labeling caught the spikes
        # With 95th percentile, spikes at 150, 145, 160 should be flagged
        assert anomalies[10] is True, "Spike at index 10 should be labeled as anomaly"
        assert anomalies[50] is True, "Spike at index 50 should be labeled as anomaly"
        assert anomalies[90] is True, "Spike at index 90 should be labeled as anomaly"
        
        # Verify some normal values are not flagged
        normal_indices = [0, 1, 2, 5, 20, 30, 40, 60, 70, 80]
        for idx in normal_indices:
            assert anomalies[idx] is False, f"Normal value at index {idx} should not be flagged"
        
        # Verify threshold is reasonable (should be around 100-110 for 95th percentile)
        # Count how many are flagged
        flagged_count = sum(anomalies)
        assert 3 <= flagged_count <= 10, f"Expected 3-10 anomalies (top 5%), got {flagged_count}"
        
    finally:
        csv_file.unlink()


def test_csv_with_existing_anomaly_column():
    """Test CSVDataLoader uses existing anomaly column when present."""
    # Create CSV with explicit anomaly column
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["value", "is_anomaly"])
        writer.writeheader()
        writer.writerow({"value": "50.0", "is_anomaly": "False"})
        writer.writerow({"value": "120.0", "is_anomaly": "True"})
        writer.writerow({"value": "45.0", "is_anomaly": "False"})
        
        csv_file = Path(f.name)
    
    try:
        loader = CSVDataLoader(
            path=csv_file,
            value_column="value",
            anomaly_column="is_anomaly",  # Column exists
        )
        
        values, anomalies = loader.load()
        
        # Should use existing column, not auto-label
        assert len(values) == 3
        assert anomalies[0] is False
        assert anomalies[1] is True
        assert anomalies[2] is False
        
    finally:
        csv_file.unlink()


def test_csv_auto_labeling_percentile():
    """Test different percentile thresholds produce different results."""
    # Create data with clear outliers
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["value"])
        writer.writeheader()
        
        # 90 normal values, 10 outliers
        for i in range(90):
            writer.writerow({"value": 50.0 + i * 0.1})
        for i in range(10):
            writer.writerow({"value": 200.0 + i * 10.0})  # Clear outliers
        
        csv_file = Path(f.name)
    
    try:
        # Test with 90th percentile (should flag ~10 values)
        loader_90 = CSVDataLoader(
            path=csv_file,
            value_column="value",
            anomaly_column=None,
            auto_label_percentile=0.90,
        )
        values_90, anomalies_90 = loader_90.load()
        flagged_90 = sum(anomalies_90)
        
        # Test with 95th percentile (should flag ~5 values)
        loader_95 = CSVDataLoader(
            path=csv_file,
            value_column="value",
            anomaly_column=None,
            auto_label_percentile=0.95,
        )
        values_95, anomalies_95 = loader_95.load()
        flagged_95 = sum(anomalies_95)
        
        # Higher percentile should flag fewer values
        assert flagged_95 <= flagged_90, "95th percentile should flag fewer than 90th"
        assert flagged_90 >= 8, "90th percentile should flag most outliers"
        
    finally:
        csv_file.unlink()
