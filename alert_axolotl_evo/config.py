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
class FitnessAlignmentConfig:
    """
    Operational constraints encoded in fitness alignment.
    
    This configuration defines the thresholds for Metric-Aligned Semantic Program
    Synthesis. Each threshold maps to an operational constraint, not just a tuning
    parameter. See docs/FITNESS_ALIGNMENT.md for comprehensive documentation.
    
    Attributes:
        min_precision: Minimum precision threshold (default 0.3 = 30%)
            Human-paged alert cost model. Below this, operational cost of false
            alarms exceeds value of detection.
        
        max_fpr: Maximum false positive rate (default 0.15 = 15%)
            Operational noise tolerance. Beyond this, alert fatigue sets in.
        
        min_alert_rate: Minimum alert rate floor (default 0.002 = 0.2%)
            Deployment feasibility floor. Rules below this are effectively
            never-firing.
        
        max_alert_rate: Maximum alert rate ceiling (default 0.20 = 20%)
            Operational noise ceiling. Rules above this become too noisy.
        
        always_true_threshold: Hard limit for always-true detection (default 0.50 = 50%)
            Rules above this are "always-true collapse" and must be strictly
            dominated. Penalty scales with dataset size.
        
        min_recall: Minimum recall floor (default 0.1 = 10%)
            Minimum usefulness requirement. Rules with zero true positives
            are explicitly penalized.
    """
    min_precision: float = 0.3  # Human-paged alert cost model
    max_fpr: float = 0.15  # Operational noise tolerance
    min_alert_rate: float = 0.002  # Deployment feasibility floor
    max_alert_rate: float = 0.20  # Operational noise ceiling
    always_true_threshold: float = 0.50  # Always-true collapse detection
    min_recall: float = 0.1  # Minimum usefulness requirement


@dataclass
class DataConfig:
    """Data generation/loading parameters."""
    data_source: str = "mock"  # "mock", "csv", "json"
    data_path: Optional[Path] = None
    value_column: str = "value"  # For CSV/JSON
    timestamp_column: str = "timestamp"  # For CSV/JSON
    anomaly_column: Optional[str] = None  # For CSV/JSON
    # Mock data parameters
    mock_size: int = 1000  # Increased from 100 for more realistic dataset
    anomaly_count: int = 50  # Increased proportionally (5% rate)
    anomaly_multiplier: float = 1.8  # Reduced from 2.5 for harder detection
    # Data consistency: if True, use same data across all generations
    # If False, data changes per generation (seed + gen)
    consistent_data: bool = True  # Default to True for proper learning
    # Realistic data generation options
    use_realistic_patterns: bool = True  # Enable trends, noise, realistic anomalies
    base_latency_mean: float = 50.0  # Base latency mean
    base_latency_std: float = 10.0  # Base latency std dev
    trend_strength: float = 0.1  # Strength of gradual trends (0-1)
    noise_level: float = 0.15  # Additional noise level (0-1)


@dataclass
class Config:
    """Main configuration class."""
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    operators: OperatorsConfig = field(default_factory=OperatorsConfig)
    fitness: FitnessConfig = field(default_factory=FitnessConfig)
    fitness_alignment: FitnessAlignmentConfig = field(default_factory=FitnessAlignmentConfig)
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
        if "fitness_alignment" in data:
            config.fitness_alignment = FitnessAlignmentConfig(**data["fitness_alignment"])
        if "data" in data:
            data_dict = data["data"].copy()
            # Convert data_path string to Path if present
            if "data_path" in data_dict and data_dict["data_path"]:
                data_dict["data_path"] = Path(data_dict["data_path"])
            config.data = DataConfig(**data_dict)
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
            "fitness_alignment": {
                "min_precision": self.fitness_alignment.min_precision,
                "max_fpr": self.fitness_alignment.max_fpr,
                "min_alert_rate": self.fitness_alignment.min_alert_rate,
                "max_alert_rate": self.fitness_alignment.max_alert_rate,
                "always_true_threshold": self.fitness_alignment.always_true_threshold,
                "min_recall": self.fitness_alignment.min_recall,
            },
            "data": {
                "data_source": self.data.data_source,
                "data_path": str(self.data.data_path) if self.data.data_path else None,
                "value_column": self.data.value_column,
                "timestamp_column": self.data.timestamp_column,
                "anomaly_column": self.data.anomaly_column,
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
    parser.add_argument("--data-source", type=str, choices=["mock", "csv", "json"], help="Data source type")
    parser.add_argument("--data-path", type=Path, help="Path to data file (for csv/json)")
    parser.add_argument("--value-column", type=str, help="Column/key name for values")
    parser.add_argument("--anomaly-column", type=str, help="Column/key name for anomaly labels")
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
    if args.data_source is not None:
        config.data.data_source = args.data_source
    if args.data_path is not None:
        config.data.data_path = args.data_path
    if args.value_column is not None:
        config.data.value_column = args.value_column
    if args.anomaly_column is not None:
        config.data.anomaly_column = args.anomaly_column
    return config

