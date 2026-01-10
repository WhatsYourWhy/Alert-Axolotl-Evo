"""Example using real data (when data loading is integrated)."""

from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config
from alert_axolotl_evo.data import CSVDataLoader

if __name__ == "__main__":
    # This example shows how to use real data once integrated
    # For now, it uses mock data
    config = Config()
    
    # In the future, you could do:
    # loader = CSVDataLoader("data.csv", value_column="latency", anomaly_column="is_anomaly")
    # values, anomalies = loader.load()
    
    evolve(config=config)

