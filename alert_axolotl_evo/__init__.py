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
from alert_axolotl_evo.meta_evolution import MetaEvolver, ConfigGenome
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.analytics import (
    analyze_evolution_results,
    track_performance_metrics,
    identify_successful_configs,
)
from alert_axolotl_evo.pattern_discovery import (
    discover_common_patterns,
    suggest_new_primitives,
    analyze_primitive_usage,
)
from alert_axolotl_evo.compiler import PrimitiveCompiler
from alert_axolotl_evo.promotion import PromotionManager

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
    "MetaEvolver",
    "ConfigGenome",
    "SelfImprovingEvolver",
    "analyze_evolution_results",
    "track_performance_metrics",
    "identify_successful_configs",
    "discover_common_patterns",
    "suggest_new_primitives",
    "analyze_primitive_usage",
    "PrimitiveCompiler",
    "PromotionManager",
]

