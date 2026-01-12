"""Primitive function and terminal definitions."""

import math
from typing import Any, Callable, Dict, List


# Function definitions
FUNCTIONS: Dict[str, Callable] = {
    # Comparison operators
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    # Logical operators
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
    "not": lambda a: not a,
    # Statistical functions
    "avg": lambda vals: sum(vals) / len(vals) if vals else 0,
    "max": lambda vals: max(vals) if vals else 0,
    "min": lambda vals: min(vals) if vals else 0,
    "sum": lambda vals: sum(vals) if vals else 0,
    "count": lambda vals: len(vals) if vals else 0,
    "stddev": lambda vals: math.sqrt(sum((x - sum(vals) / len(vals)) ** 2 for x in vals) / len(vals)) if vals and len(vals) > 1 else 0,
    "percentile": lambda vals, p: sorted(vals)[int(len(vals) * p / 100)] if vals and 0 <= p <= 100 else 0,
    # Time-window functions (for rolling windows)
    "window_avg": lambda vals, n: sum(vals[-n:]) / min(n, len(vals)) if vals and n > 0 else 0,
    "window_max": lambda vals, n: max(vals[-n:]) if vals and n > 0 else 0,
    "window_min": lambda vals, n: min(vals[-n:]) if vals and n > 0 else 0,
}

ALERT = lambda cond, msg: msg if cond else None

# Message terminals (for alert messages only)
MSG_TERMINALS: List[str] = [
    "High alert!",
    "Danger zone!",
    "Anomaly detected!",
    "Threshold exceeded!",
]

# Boolean-returning functions (for condition generation)
# Note: == and != removed for continuous metrics (equality is almost always useless for floats)
# If approximate equality is needed, add a new primitive like approx_eq(value, target, tolerance)
BOOLEAN_FUNCTIONS: List[str] = [
    ">", "<", ">=", "<=",  # Comparison operators (no == or !=)
    "and", "or", "not",    # Logical operators
]

# Terminal values (backward compatibility - includes numeric, variable, and message terminals)
TERMINALS: List[Any] = [
    "latency",
    25, 50, 75, 100, 150, 200,
    "High alert!",
    "Danger zone!",
    "Anomaly detected!",
    "Threshold exceeded!",
]

# Arity mapping: function name -> number of arguments
ARITIES: Dict[str, int] = {
    "if_alert": 2,
    # Comparison operators
    ">": 2,
    "<": 2,
    ">=": 2,
    "<=": 2,
    "==": 2,
    "!=": 2,
    # Logical operators
    "and": 2,
    "or": 2,
    "not": 1,
    # Statistical functions
    "avg": 1,
    "max": 1,
    "min": 1,
    "sum": 1,
    "count": 1,
    "stddev": 1,
    "percentile": 2,  # percentile(vals, p)
    # Time-window functions
    "window_avg": 2,  # window_avg(vals, n)
    "window_max": 2,
    "window_min": 2,
}

# Function names for random selection
FUNCTION_NAMES: List[str] = [
    "if_alert",
    ">", "<", ">=", "<=", "==", "!=",
    "and", "or", "not",
    "avg", "max", "min", "sum", "count", "stddev", "percentile",
    "window_avg", "window_max", "window_min",
]


def register_function(name: str, func: Callable, arity: int, needs_context: bool = False) -> None:
    """
    Register a new function primitive.
    
    Args:
        name: Name of the primitive
        func: Python callable
        arity: Number of arguments
        needs_context: If True, evaluator passes 'data' as first arg to func(data, *args)
    """
    FUNCTIONS[name] = func
    ARITIES[name] = arity
    
    if needs_context:
        func.needs_context = True
        
    if name not in FUNCTION_NAMES:
        FUNCTION_NAMES.append(name)
        FUNCTION_NAMES.sort()  # Maintain determinism


def unregister_function(name: str) -> None:
    """Unregister a function primitive (used for pruning)."""
    if name in FUNCTIONS:
        del FUNCTIONS[name]
    if name in ARITIES:
        del ARITIES[name]
    if name in FUNCTION_NAMES:
        FUNCTION_NAMES.remove(name)
        # No need to re-sort after removal


def register_terminal(value: Any) -> None:
    """Register a terminal value (literals only)."""
    if value not in TERMINALS:
        TERMINALS.append(value)

