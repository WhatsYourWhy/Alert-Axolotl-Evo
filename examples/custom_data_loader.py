"""
Example: Injecting custom data programmatically.

This demonstrates how to inject external data without writing to files.
"""
from typing import List, Tuple

from alert_axolotl_evo.data import DataLoader
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config


class InMemoryDataLoader(DataLoader):
    """Custom DataLoader that uses in-memory data."""
    
    def __init__(self, values: List[float], anomalies: List[bool]):
        """
        Args:
            values: List of numeric values
            anomalies: List of boolean anomaly labels (must match length of values)
        """
        if len(values) != len(anomalies):
            raise ValueError("values and anomalies must have the same length")
        self.values = values
        self.anomalies = anomalies
    
    def load(self) -> Tuple[List[float], List[bool]]:
        """Return the in-memory data."""
        return self.values, self.anomalies


class StreamingDataLoader(DataLoader):
    """Example: DataLoader that fetches data from an external source."""
    
    def __init__(self, api_url: str):
        """
        Args:
            api_url: URL to fetch data from (example - not implemented)
        """
        self.api_url = api_url
        # In a real implementation, you would fetch data here or in load()
    
    def load(self) -> Tuple[List[float], List[bool]]:
        """Fetch and return data from external source."""
        # Example implementation - in practice, you'd fetch from API/database/etc.
        # For demonstration, returning mock data
        import random
        rng = random.Random(42)
        values = [rng.gauss(50, 10) for _ in range(100)]
        anomalies = [v > 80 for v in values]  # Simple threshold-based anomalies
        return values, anomalies


if __name__ == "__main__":
    # Example 1: Inject data from memory
    print("Example 1: In-memory data injection")
    custom_values = [45.2, 48.1, 52.3, 125.8, 49.5, 47.2, 135.1, 50.3]
    custom_anomalies = [False, False, False, True, False, False, True, False]
    
    in_memory_loader = InMemoryDataLoader(custom_values, custom_anomalies)
    
    config = Config()
    config.evolution.pop_size = 20
    config.evolution.generations = 10
    
    # Inject custom data loader directly
    evolve(config=config, data_loader=in_memory_loader)
    
    print("\n" + "="*60)
    print("Example 2: Streaming data loader (conceptual)")
    print("="*60)
    
    # Example 2: Custom loader from external source
    # streaming_loader = StreamingDataLoader("https://api.example.com/data")
    # evolve(config=config, data_loader=streaming_loader)
    
    print("Note: StreamingDataLoader is a template - implement API calls as needed")
