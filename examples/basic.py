"""Minimal evolution run. Exports champion to ./champion.json."""

from pathlib import Path

from alert_axolotl_evo import Config, evolve


if __name__ == "__main__":
    config = Config()
    config.evolution.seed = 42
    config.evolution.pop_size = 20
    config.evolution.generations = 5
    evolve(config=config, export_rule_path=Path("champion.json"))
