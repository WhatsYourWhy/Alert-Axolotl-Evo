"""Example using real data."""

import json
import tempfile
from pathlib import Path

from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config

if __name__ == "__main__":
    # Create sample JSON data file
    sample_data = [
        {"value": 45.2, "timestamp": "2024-01-01T00:00:00", "is_anomaly": False},
        {"value": 48.1, "timestamp": "2024-01-01T00:01:00", "is_anomaly": False},
        {"value": 52.3, "timestamp": "2024-01-01T00:02:00", "is_anomaly": False},
        {"value": 125.8, "timestamp": "2024-01-01T00:03:00", "is_anomaly": True},  # Anomaly
        {"value": 49.5, "timestamp": "2024-01-01T00:04:00", "is_anomaly": False},
        {"value": 47.2, "timestamp": "2024-01-01T00:05:00", "is_anomaly": False},
        {"value": 135.1, "timestamp": "2024-01-01T00:06:00", "is_anomaly": True},  # Anomaly
        {"value": 50.3, "timestamp": "2024-01-01T00:07:00", "is_anomaly": False},
    ]
    
    # Create temporary JSON file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_data, f)
        data_file = Path(f.name)
    
    try:
        config = Config()
        config.data.data_source = "json"
        config.data.data_path = data_file
        config.data.value_column = "value"
        config.data.anomaly_column = "is_anomaly"
        config.evolution.pop_size = 20
        config.evolution.generations = 10
        
        print(f"Using data from: {data_file}")
        evolve(config=config)
    finally:
        # Clean up
        data_file.unlink()
