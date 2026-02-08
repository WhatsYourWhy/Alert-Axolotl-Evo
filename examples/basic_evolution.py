"""Basic evolution example."""

from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config

if __name__ == "__main__":
    config = Config()
    config.evolution.pop_size = 30
    config.evolution.generations = 20
    evolve(config=config)

