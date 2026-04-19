"""Alert-Axolotl-Evo — deterministic genetic programming for alert rules."""

from alert_axolotl_evo.config import Config, load_config
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.persistence import load_rule, save_rule

__version__ = "1.0.0"

__all__ = [
    "Config",
    "load_config",
    "evolve",
    "load_rule",
    "save_rule",
    "__version__",
]
