"""Tree evaluation and synthetic data generation."""

import random
from typing import Any, Callable, Dict, List, Optional, Tuple

from alert_axolotl_evo.primitives import ALERT, ARITIES, FUNCTIONS


def generate_mock_data(
    seed: int,
    size: int = 100,
    anomaly_count: int = 8,
    anomaly_multiplier: float = 2.5,
) -> Tuple[List[float], List[bool]]:
    """Generate deterministic mock latency data with anomalies."""
    rng = random.Random(seed)
    values = [rng.gauss(50, 10) for _ in range(size)]
    anomaly_idx = set(rng.sample(range(size), anomaly_count))
    anomalies = []
    for idx, value in enumerate(values):
        if idx in anomaly_idx:
            values[idx] = value * anomaly_multiplier
            anomalies.append(True)
        else:
            anomalies.append(False)
    return values, anomalies


def coerce_number(value: Any) -> Optional[float]:
    """Coerce numeric input to float. Non-numeric returns None (not 0.0)."""
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _call_standard_function(op: str, args: List[Any], func: Callable) -> Any:
    """Dispatch a primitive call with strict type enforcement.

    Invariants:
    - Comparisons require numeric inputs; any non-numeric yields None.
    - Logical ops require bool inputs; non-bool yields None.
    - Statistical/window ops require a list; scalars yield None.
    """
    if op == "not":
        a_val = args[0]
        if type(a_val) is not bool:
            return None
        return func(a_val)

    if op in ("avg", "max", "min", "sum", "count", "stddev"):
        if isinstance(args[0], list):
            numeric = [coerce_number(item) for item in args[0] if item is not None]
            return func(numeric) if numeric else 0
        return None

    if op == "percentile":
        vals = args[0]
        p = coerce_number(args[1])
        if p is None:
            return None
        if isinstance(vals, list):
            numeric = [coerce_number(item) for item in vals if item is not None]
            numeric = [n for n in numeric if n is not None]
            return func(numeric, p) if numeric else None
        return None

    if op in ("window_avg", "window_max", "window_min"):
        vals = args[0]
        n_val = coerce_number(args[1])
        if n_val is None:
            return None
        n = int(n_val)
        if isinstance(vals, list):
            numeric = [coerce_number(item) for item in vals if item is not None]
            numeric = [n for n in numeric if n is not None]
            return func(numeric, n) if numeric else None
        return None

    if op in (">", "<", ">=", "<=", "==", "!="):
        a = coerce_number(args[0])
        b = coerce_number(args[1])
        if a is None or b is None:
            return None
        result = func(a, b)
        if type(result) is not bool:
            return None
        return result

    if op in ("and", "or"):
        a_val = args[0]
        b_val = args[1]
        if type(a_val) is not bool or type(b_val) is not bool:
            return None
        return func(a_val, b_val)

    return func(*args)


def _evaluate(tree: Any, data: Dict[str, Any]) -> Any:
    """Recursive tree evaluation with macro support.

    Invalid `if_alert` conditions/messages return sentinel tuples
    (`__INVALID_CONDITION__`/`__INVALID_MESSAGE__`) so the fitness layer
    can count them without conflating them with a no-alert outcome.
    """
    if isinstance(tree, list):
        return [_evaluate(item, data) for item in tree]

    if not isinstance(tree, tuple):
        if isinstance(tree, str) and tree in data:
            return data[tree]
        return tree

    if not tree:
        return None

    op = tree[0]

    if op == "if_alert":
        if len(tree) != 3:
            return None
        cond_val = _evaluate(tree[1], data)
        msg = _evaluate(tree[2], data)

        if type(cond_val) is not bool:
            return ("__INVALID_CONDITION__", cond_val, msg)

        if not isinstance(msg, str):
            return ("__INVALID_MESSAGE__", cond_val, msg)

        return ALERT(cond_val, msg)

    func = FUNCTIONS.get(op)
    if func:
        expected_arity = ARITIES.get(op)
        if expected_arity is not None:
            actual_arity = len(tree) - 1
            if expected_arity != actual_arity:
                # 0 instead of None: None crashes comparisons downstream.
                return 0

        try:
            args = [_evaluate(child, data) for child in tree[1:]]
        except Exception:
            return None

        try:
            if getattr(func, "needs_context", False):
                return func(data, *args)
            return _call_standard_function(op, args, func)
        except Exception:
            return None

    return None


def evaluate(tree: Any, data: Dict[str, Any]) -> Any:
    """Evaluate a tree, catching any unexpected exceptions."""
    try:
        return _evaluate(tree, data)
    except Exception:
        return None
