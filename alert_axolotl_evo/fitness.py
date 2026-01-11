"""Fitness evaluation and tree evaluation."""

import random
from typing import Any, Dict, List, Optional, Tuple

from alert_axolotl_evo.config import DataConfig, FitnessConfig
from alert_axolotl_evo.data import DataLoader, MockDataLoader
from alert_axolotl_evo.primitives import ALERT, FUNCTIONS


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


def _evaluate(tree: Any, data: Dict[str, Any]) -> Any:
    """Recursively evaluate a tree."""
    if isinstance(tree, list):
        return [_evaluate(item, data) for item in tree]
    if isinstance(tree, tuple):
        if not tree:
            return None
        op = tree[0]
        
        # Handle if_alert
        if op == "if_alert":
            if len(tree) != 3:
                return None
            cond = _evaluate(tree[1], data)
            msg = _evaluate(tree[2], data)
            return ALERT(bool(cond), msg)
        
        # Handle unary functions
        if op == "not":
            if len(tree) != 2:
                return None
            val = _evaluate(tree[1], data)
            return FUNCTIONS[op](bool(val))
        
        # Handle single-argument statistical functions
        if op in ("avg", "max", "min", "sum", "count", "stddev"):
            if len(tree) != 2:
                return None
            vals = _evaluate(tree[1], data)
            if isinstance(vals, list):
                numeric = [coerce_number(item) for item in vals if item is not None]
                return FUNCTIONS[op](numeric) if numeric else 0
            return FUNCTIONS[op]([coerce_number(vals)])
        
        # Handle percentile (2 args: vals, percentile)
        if op == "percentile":
            if len(tree) != 3:
                return None
            vals = _evaluate(tree[1], data)
            p = coerce_number(_evaluate(tree[2], data))
            if isinstance(vals, list):
                numeric = [coerce_number(item) for item in vals if item is not None]
                return FUNCTIONS[op](numeric, p) if numeric else 0
            return 0
        
        # Handle window functions (2 args: vals, window_size)
        if op in ("window_avg", "window_max", "window_min"):
            if len(tree) != 3:
                return None
            vals = _evaluate(tree[1], data)
            n = int(coerce_number(_evaluate(tree[2], data)))
            if isinstance(vals, list):
                numeric = [coerce_number(item) for item in vals if item is not None]
                return FUNCTIONS[op](numeric, n) if numeric else 0
            return 0
        
        # Handle binary comparison operators
        if op in (">", "<", ">=", "<=", "==", "!="):
            if len(tree) != 3:
                return None
            left = _evaluate(tree[1], data)
            right = _evaluate(tree[2], data)
            return FUNCTIONS[op](coerce_number(left), coerce_number(right))
        
        # Handle binary logical operators
        if op in ("and", "or"):
            if len(tree) != 3:
                return None
            left = _evaluate(tree[1], data)
            right = _evaluate(tree[2], data)
            return FUNCTIONS[op](bool(left), bool(right))
        
        # Unknown operator
        return None
    
    if isinstance(tree, str) and tree in data:
        return data[tree]
    return tree


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

