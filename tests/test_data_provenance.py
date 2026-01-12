"""
Test provenance metadata for CSVDataLoader auto-labeling.
"""
import csv
import tempfile
from pathlib import Path

import pytest

from alert_axolotl_evo.data import CSVDataLoader


def test_provenance_metadata_auto_labeling():
    """Test that provenance metadata is set when auto-labeling occurs."""
    # Create CSV without anomaly column
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["value"])
        writer.writeheader()
        for i in range(10):
            writer.writerow({"value": 50.0 + i})
        writer.writerow({"value": 200.0})  # Outlier
        
        csv_file = Path(f.name)
    
    try:
        loader = CSVDataLoader(
            path=csv_file,
            value_column="value",
            anomaly_column=None,  # Explicitly no labels
            auto_label_percentile=0.90,
        )
        
        values, anomalies = loader.load()
        
        # Check provenance metadata
        provenance = loader.get_label_provenance()
        assert provenance["label_source"] == "auto_percentile"
        assert provenance["label_threshold"] is not None
        assert isinstance(provenance["label_threshold"], float)
        
    finally:
        csv_file.unlink()


def test_provenance_metadata_explicit_labels():
    """Test that provenance metadata indicates explicit labels when column exists."""
    # Create CSV with anomaly column
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["value", "is_anomaly"])
        writer.writeheader()
        writer.writerow({"value": "50.0", "is_anomaly": "False"})
        writer.writerow({"value": "120.0", "is_anomaly": "True"})
        
        csv_file = Path(f.name)
    
    try:
        loader = CSVDataLoader(
            path=csv_file,
            value_column="value",
            anomaly_column="is_anomaly",  # Column exists
        )
        
        values, anomalies = loader.load()
        
        # Check provenance metadata
        provenance = loader.get_label_provenance()
        assert provenance["label_source"] == "explicit"
        assert provenance["label_threshold"] is None
        
    finally:
        csv_file.unlink()


def test_provenance_metadata_missing_column():
    """Test that provenance metadata is set when column is specified but missing in file."""
    # Create CSV without anomaly column (but we specify one)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["value"])
        writer.writeheader()
        writer.writerow({"value": "50.0"})
        
        csv_file = Path(f.name)
    
    try:
        loader = CSVDataLoader(
            path=csv_file,
            value_column="value",
            anomaly_column="is_anomaly",  # Specified but doesn't exist in file
            auto_label_percentile=0.95,
        )
        
        values, anomalies = loader.load()
        
        # Should auto-label since column is missing
        provenance = loader.get_label_provenance()
        assert provenance["label_source"] == "auto_percentile"
        assert provenance["label_threshold"] is not None
        
    finally:
        csv_file.unlink()
