"""Configuration management."""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class EvolutionConfig:
    """Evolution parameters."""
    seed: int = 42
    pop_size: int = 50
    generations: int = 40
    min_depth: int = 2
    max_depth: int = 7
    elite_ratio: float = 0.1


@dataclass
class OperatorsConfig:
    """Genetic operator parameters."""
    crossover_rate: float = 0.9
    mutation_rate: float = 0.2
    tournament_size: int = 4


@dataclass
class FitnessConfig:
    """Fitness evaluation parameters."""
    beta: float = 0.5
    bloat_penalty: float = 0.005
    fp_threshold: int = 40
    fp_penalty: float = 5.0


@dataclass
class DataConfig:
    """Data generation/loading parameters."""
    mock_size: int = 100
    anomaly_count: int = 8
    anomaly_multiplier: float = 2.5


@dataclass
class Config:
    """Main configuration class."""
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    operators: OperatorsConfig = field(default_factory=OperatorsConfig)
    fitness: FitnessConfig = field(default_factory=FitnessConfig)
    data: DataConfig = field(default_factory=DataConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create Config from dictionary."""
        config = cls()
        if "evolution" in data:
            config.evolution = EvolutionConfig(**data["evolution"])
        if "operators" in data:
            config.operators = OperatorsConfig(**data["operators"])
        if "fitness" in data:
            config.fitness = FitnessConfig(**data["fitness"])
        if "data" in data:
            config.data = DataConfig(**data["data"])
        return config

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """Load Config from YAML file."""
        try:
            import yaml
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data)
        except ImportError:
            raise ImportError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
        except Exception as e:
            raise ValueError(f"Failed to load YAML config: {e}")

    @classmethod
    def from_json(cls, path: Path) -> "Config":
        """Load Config from JSON file."""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            raise ValueError(f"Failed to load JSON config: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert Config to dictionary."""
        return {
            "evolution": {
                "seed": self.evolution.seed,
                "pop_size": self.evolution.pop_size,
                "generations": self.evolution.generations,
                "min_depth": self.evolution.min_depth,
                "max_depth": self.evolution.max_depth,
                "elite_ratio": self.evolution.elite_ratio,
            },
            "operators": {
                "crossover_rate": self.operators.crossover_rate,
                "mutation_rate": self.operators.mutation_rate,
                "tournament_size": self.operators.tournament_size,
            },
            "fitness": {
                "beta": self.fitness.beta,
                "bloat_penalty": self.fitness.bloat_penalty,
                "fp_threshold": self.fitness.fp_threshold,
                "fp_penalty": self.fitness.fp_penalty,
            },
            "data": {
                "mock_size": self.data.mock_size,
                "anomaly_count": self.data.anomaly_count,
                "anomaly_multiplier": self.data.anomaly_multiplier,
            },
        }


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from file or return defaults."""
    if config_path is None:
        # Try to find config.yaml in current directory
        config_path = Path("config.yaml")
        if not config_path.exists():
            return Config()
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    if config_path.suffix == ".yaml" or config_path.suffix == ".yml":
        return Config.from_yaml(config_path)
    elif config_path.suffix == ".json":
        return Config.from_json(config_path)
    else:
        raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def add_config_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Add configuration-related arguments to argument parser."""
    parser.add_argument("--config", type=Path, help="Path to configuration file (YAML or JSON)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--pop-size", type=int, help="Population size")
    parser.add_argument("--generations", type=int, help="Number of generations")
    parser.add_argument("--min-depth", type=int, help="Minimum tree depth")
    parser.add_argument("--max-depth", type=int, help="Maximum tree depth")
    parser.add_argument("--crossover-rate", type=float, help="Crossover rate")
    parser.add_argument("--mutation-rate", type=float, help="Mutation rate")
    parser.add_argument("--tournament-size", type=int, help="Tournament size")
    return parser


def merge_cli_args(config: Config, args: argparse.Namespace) -> Config:
    """Merge CLI arguments into config, overriding file values."""
    if args.seed is not None:
        config.evolution.seed = args.seed
    if args.pop_size is not None:
        config.evolution.pop_size = args.pop_size
    if args.generations is not None:
        config.evolution.generations = args.generations
    if args.min_depth is not None:
        config.evolution.min_depth = args.min_depth
    if args.max_depth is not None:
        config.evolution.max_depth = args.max_depth
    if args.crossover_rate is not None:
        config.operators.crossover_rate = args.crossover_rate
    if args.mutation_rate is not None:
        config.operators.mutation_rate = args.mutation_rate
    if args.tournament_size is not None:
        config.operators.tournament_size = args.tournament_size
    return config

