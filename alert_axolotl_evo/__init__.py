"""Alert Axolotl Evo: a deterministic, gamified genetic programming system."""

from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.fitness import evaluate, fitness
from alert_axolotl_evo.tree import node_count, tree_hash
from alert_axolotl_evo.primitives import (
    ARITIES,
    FUNCTIONS,
    FUNCTION_NAMES,
    TERMINALS,
    register_function,
    register_terminal,
)
from alert_axolotl_evo.config import Config, load_config
from alert_axolotl_evo.persistence import load_rule, save_rule

__all__ = [
    "evolve",
    "evaluate",
    "fitness",
    "node_count",
    "tree_hash",
    "ARITIES",
    "FUNCTIONS",
    "FUNCTION_NAMES",
    "TERMINALS",
    "register_function",
    "register_terminal",
    "Config",
    "load_config",
    "load_rule",
    "save_rule",
]

