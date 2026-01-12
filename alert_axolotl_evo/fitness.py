"""Fitness evaluation and tree evaluation."""

import random
from typing import Any, Callable, Dict, List, Optional, Tuple

from alert_axolotl_evo.config import DataConfig, FitnessConfig
from alert_axolotl_evo.data import DataLoader, MockDataLoader
from alert_axolotl_evo.primitives import ALERT, FUNCTIONS, ARITIES


def generate_mock_data(seed: int, size: int = 100, anomaly_count: int = 8, anomaly_multiplier: float = 2.5) -> Tuple[List[float], List[bool]]:
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


def coerce_number(value: Any) -> float:
    """Coerce a value to a number."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):
        numeric = [coerce_number(item) for item in value if item is not None]
        return FUNCTIONS["avg"](numeric)
    return 0.0


def _call_standard_function(op: str, args: List[Any], func: Callable) -> Any:
    """Call standard functions with appropriate type coercion."""
    # Handle unary functions
    if op == "not":
        return func(bool(args[0]))
    
    # Handle statistical functions (expect list)
    if op in ("avg", "max", "min", "sum", "count", "stddev"):
        if isinstance(args[0], list):
            numeric = [coerce_number(item) for item in args[0] if item is not None]
            return func(numeric) if numeric else 0
        return func([coerce_number(args[0])])
    
    # Handle percentile
    if op == "percentile":
        vals = args[0]
        p = coerce_number(args[1])
        if isinstance(vals, list):
            numeric = [coerce_number(item) for item in vals if item is not None]
            return func(numeric, p) if numeric else 0
        return 0
    
    # Handle window functions
    if op in ("window_avg", "window_max", "window_min"):
        vals = args[0]
        n = int(coerce_number(args[1]))
        if isinstance(vals, list):
            numeric = [coerce_number(item) for item in vals if item is not None]
            return func(numeric, n) if numeric else 0
        return 0
    
    # Handle binary comparison operators
    if op in (">", "<", ">=", "<=", "==", "!="):
        return func(coerce_number(args[0]), coerce_number(args[1]))
    
    # Handle binary logical operators
    if op in ("and", "or"):
        return func(bool(args[0]), bool(args[1]))
    
    # Fallback: try direct call
    return func(*args)


def _evaluate(tree: Any, data: Dict[str, Any]) -> Any:
    """
    Recursively evaluate a tree with macro support.
    Supports standard GP functions and Context-Aware Macros (0-arity).
    """
    # 1. Handle Lists (Batch Eval)
    if isinstance(tree, list):
        return [_evaluate(item, data) for item in tree]

    # 2. Handle Terminals (Leaves)
    if not isinstance(tree, tuple):
        if isinstance(tree, str) and tree in data:
            return data[tree]
        return tree
    
    if not tree:
        return None

    op = tree[0]

    # 3. Handle Special 'if_alert' (returns string or None)
    if op == "if_alert":
        if len(tree) != 3:
            return None
        cond = _evaluate(tree[1], data)
        msg = _evaluate(tree[2], data)
        return ALERT(bool(cond), msg)

    # 4. Generic Function Dispatch (supports macros)
    func = FUNCTIONS.get(op)
    if func:
        # CRITICAL FIX: Arity enforcement
        expected_arity = ARITIES.get(op)
        if expected_arity is not None:
            actual_arity = len(tree) - 1
            if expected_arity != actual_arity:
                # Wrong arity - return 0 (safe penalized value)
                # None can propagate weirdly or crash comparisons in GP fitness evaluation
                return 0
        
        # Evaluate children first (Standard GP)
        # Note: For 0-arity macros, args will be empty.
        try:
            args = [_evaluate(child, data) for child in tree[1:]]
        except Exception:
            # Graceful failure for child eval errors
            return None

        try:
            # MACRO DISPATCH: Inject context if requested
            if getattr(func, "needs_context", False):
                return func(data, *args)
            else:
                # Standard function dispatch
                return _call_standard_function(op, args, func)
        except Exception:
            # Runtime protection (e.g. div/0, type errors)
            return None

    # Unknown operator
    return None


def evaluate(tree: Any, data: Dict[str, Any]) -> Any:
    """Recursively evaluate a tree with error handling."""
    try:
        return _evaluate(tree, data)
    except Exception:
        return None


def fitness(
    tree: Any,
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> float:
    """Compute fitness based on detection quality and parsimony."""
    if fitness_config is None:
        fitness_config = FitnessConfig()
    if data_config is None:
        data_config = DataConfig()
    
    # Use provided data loader or create mock data
    if data_loader is not None:
        if isinstance(data_loader, MockDataLoader):
            # Update seed for mock data loader
            data_loader.seed = seed + gen
        values, anomalies = data_loader.load()
    else:
        # Fallback to generate_mock_data for backward compatibility
        values, anomalies = generate_mock_data(
            seed + gen,
            size=data_config.mock_size,
            anomaly_count=data_config.anomaly_count,
            anomaly_multiplier=data_config.anomaly_multiplier,
        )
    tp = fp = fn = 0
    for idx, value in enumerate(values):
        window_size = 5 + (idx % 2)
        start = max(0, idx - window_size + 1)
        window = values[start : idx + 1]
        data = {"latency": window}
        result = evaluate(tree, data)
        alerting = isinstance(result, str)
        if anomalies[idx] and alerting:
            tp += 1
        if anomalies[idx] and not alerting:
            fn += 1
        if not anomalies[idx] and alerting:
            fp += 1
    # Calculate possible_tp from actual anomalies in data
    possible_tp = sum(anomalies) if anomalies else data_config.anomaly_count
    tp_rate = tp / possible_tp if possible_tp > 0 else 0.0
    fp_rate = fp / possible_tp if possible_tp > 0 else 0.0
    fn_rate = fn / possible_tp if possible_tp > 0 else 0.0
    beta = fitness_config.beta
    beta_sq = beta**2
    denom = (1 + beta_sq) * tp_rate + beta_sq * fn_rate + fp_rate
    f_beta = ((1 + beta_sq) * tp_rate / denom) if denom else 0.0
    score = f_beta * possible_tp
    if "avg" in str(tree):
        score += 1.0
    if "avg" in str(tree) and ">" in str(tree):
        score += 1.5
    if fp > fitness_config.fp_threshold:
        score -= fitness_config.fp_penalty
    penalty = fitness_config.bloat_penalty * len(str(tree))
    return score - penalty

