"""Quick test to verify external data injection works."""
from alert_axolotl_evo.data import DataLoader
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config
from typing import List, Tuple


class TestExternalDataLoader(DataLoader):
    """Test loader that injects external data."""
    
    def load(self) -> Tuple[List[float], List[bool]]:
        # Simulate external data (e.g., from API, database, etc.)
        values = [45.2, 48.1, 52.3, 125.8, 49.5, 47.2, 135.1, 50.3, 46.8, 51.2]
        anomalies = [False, False, False, True, False, False, True, False, False, False]
        return values, anomalies


if __name__ == "__main__":
    print("Testing external data injection...")
    
    # Create custom loader with external data
    external_loader = TestExternalDataLoader()
    
    # Verify loader works
    values, anomalies = external_loader.load()
    print(f"[OK] Loader works: {len(values)} values, {sum(anomalies)} anomalies")
    
    # Test with evolution (small run)
    config = Config()
    config.evolution.pop_size = 10
    config.evolution.generations = 3
    
    print("\nRunning evolution with external data loader...")
    print("(This will take a moment)")
    
    # Inject external data loader
    evolve(config=config, data_loader=external_loader)
    
    print("\n[OK] External data injection verified!")
