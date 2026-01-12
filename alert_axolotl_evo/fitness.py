"""Fitness evaluation and tree evaluation."""

import random
from typing import Any, Callable, Dict, List, Optional, Tuple

from alert_axolotl_evo.config import DataConfig, FitnessConfig
from alert_axolotl_evo.data import DataLoader, MockDataLoader
from alert_axolotl_evo.primitives import ALERT, FUNCTIONS, ARITIES
from alert_axolotl_evo.tree import is_valid_alert_rule, node_count


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


def coerce_number(value: Any) -> Optional[float]:
    """
    Coerce a value to a number.
    
    Only coerce numeric types (int, float). Returns None for non-numeric types.
    List averaging is removed - if averaging is needed, use avg/window_avg explicitly.
    """
    if isinstance(value, (int, float)):
        return float(value)
    # Return None for non-numeric types (not 0.0)
    return None


def _call_standard_function(op: str, args: List[Any], func: Callable) -> Any:
    """Call standard functions with appropriate type coercion."""
    # Handle unary functions
    if op == "not":
        # STRICT: arg must be bool, not truthy
        a_val = args[0]
        if type(a_val) is not bool:
            return None  # Invalid: not() requires bool input
        return func(a_val)
    
    # Handle statistical functions (expect list - semantic validity enforcement)
    if op in ("avg", "max", "min", "sum", "count", "stddev"):
        if isinstance(args[0], list):
            numeric = [coerce_number(item) for item in args[0] if item is not None]
            return func(numeric) if numeric else 0
        # SEMANTIC FIX: Statistical functions require lists, not scalars
        # Return None to indicate invalid semantics (will be treated as no alert)
        return None
    
    # Handle percentile
    if op == "percentile":
        vals = args[0]
        p = coerce_number(args[1])
        if p is None:
            return None
        if isinstance(vals, list):
            numeric = [coerce_number(item) for item in vals if item is not None]
            numeric = [n for n in numeric if n is not None]
            return func(numeric, p) if numeric else None
        # Return None for invalid input (not 0)
        return None
    
    # Handle window functions
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
        # Return None for invalid input (not 0)
        return None
    
    # Handle binary comparison operators
    if op in (">", "<", ">=", "<=", "==", "!="):
        a = coerce_number(args[0])
        b = coerce_number(args[1])
        if a is None or b is None:
            return None
        return func(a, b)
    
    # Handle binary logical operators
    if op in ("and", "or"):
        # STRICT: both args must be bool, not truthy
        a_val = args[0]
        b_val = args[1]
        if type(a_val) is not bool or type(b_val) is not bool:
            return None  # Invalid: and/or require bool inputs
        return func(a_val, b_val)
    
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
        cond_val = _evaluate(tree[1], data)
        msg = _evaluate(tree[2], data)
        
        # STRICT: condition must be bool, not truthy
        # This prevents strings/numbers from being "always true"
        if type(cond_val) is not bool:
            return None  # Invalid condition - treat as no alert
        
        # Message must be a string
        if not isinstance(msg, str):
            return None  # Invalid message
        
        return ALERT(cond_val, msg)

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


def fitness_breakdown(
    tree: Any,
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> Dict[str, Any]:
    """
    Compute fitness and return detailed breakdown for debugging.
    
    Returns:
        Dictionary with keys: fitness, tp, fp, fn, tp_rate, fp_rate, fn_rate, f_beta, score, penalty
    """
    if fitness_config is None:
        fitness_config = FitnessConfig()
    if data_config is None:
        data_config = DataConfig()
    
    # Use provided data loader or create mock data
    if data_loader is not None:
        if isinstance(data_loader, MockDataLoader):
            # Update seed based on consistent_data config
            consistent_data = getattr(data_config, 'consistent_data', True)
            if consistent_data:
                data_loader.seed = seed
            else:
                data_loader.seed = seed + gen
        values, anomalies = data_loader.load()
        assert isinstance(values, list), "values must be a list"
        assert isinstance(anomalies, list), "anomalies must be a list"
        assert len(values) == len(anomalies), "values and anomalies must have same length"
        assert all(isinstance(v, (int, float)) for v in values), "values must be numeric"
        assert all(isinstance(a, bool) for a in anomalies), "anomalies must be boolean"
    else:
        # Fallback to generate_mock_data for backward compatibility
        consistent_data = getattr(data_config, 'consistent_data', True)
        data_seed = seed if consistent_data else seed + gen
        values, anomalies = generate_mock_data(
            data_seed,
            size=data_config.mock_size,
            anomaly_count=data_config.anomaly_count,
            anomaly_multiplier=data_config.anomaly_multiplier,
        )
    
    tp = fp = fn = 0
    invalid_output_count = 0
    for idx, value in enumerate(values):
        window_size = 5 + (idx % 2)
        start = max(0, idx - window_size + 1)
        window = values[start : idx + 1]
        data = {"latency": window}
        result = evaluate(tree, data)
        
        # HARD VALIDITY GATE: Check output validity
        # Valid output is str (alert message) or None (no alert)
        if result is not None and not isinstance(result, str):
            invalid_output_count += 1
            # If we get invalid output, treat as no alert for this iteration
            result = None
        
        alerting = isinstance(result, str)
        if anomalies[idx] and alerting:
            tp += 1
        if anomalies[idx] and not alerting:
            fn += 1
        if not anomalies[idx] and alerting:
            fp += 1
    
    # Calculate metrics
    total_rows = len(values)
    alert_rate = (tp + fp) / total_rows if total_rows > 0 else 0.0
    invalid_rate = invalid_output_count / total_rows if total_rows > 0 else 0.0
    
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
    
    # SOFT PENALTY: Penalize invalid outputs
    if invalid_rate > 0.0:
        score -= 0.5 * invalid_rate
    
    # NO-ALERT PENALTY: Trees that never alert are useless
    if tp == 0 and fp == 0:
        score -= 5.0  # Explicit penalty that dominates bloat incentives
    
    # ALERT-RATE BAND PENALTY
    if alert_rate < 0.002:  # Less than 0.2%
        score -= 2.0
    elif alert_rate > 0.50:  # More than 50% - "always-true collapse"
        # Heavy penalty that scales with alert rate and dataset size
        excess_rate = alert_rate - 0.5
        penalty = 2.0 * excess_rate * total_rows
        score -= penalty
    elif alert_rate > 0.20:  # More than 20% but <= 50%
        score -= 3.0
    
    # MINIMUM TP FLOOR
    if possible_tp > 0:
        recall = tp / possible_tp
        if recall < 0.1 and tp == 0:
            score -= 3.0
    
    if fp > fitness_config.fp_threshold:
        score -= fitness_config.fp_penalty
    penalty = fitness_config.bloat_penalty * node_count(tree)
    final_fitness = score - penalty
    
    return {
        "fitness": final_fitness,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "possible_tp": possible_tp,
        "tp_rate": tp_rate,
        "fp_rate": fp_rate,
        "fn_rate": fn_rate,
        "f_beta": f_beta,
        "score": score,
        "penalty": penalty,
        "alert_rate": alert_rate,
        "invalid_rate": invalid_rate,
        "node_count": node_count(tree),
    }


def fitness(
    tree: Any,
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> float:
    """
    Compute fitness based on detection quality and parsimony.
    
    NOTE: fitness must be pure and side-effect free.
    This function computes a score based on tree evaluation and data.
    It does not modify global state, registries, or learning mechanisms.
    """
    if fitness_config is None:
        fitness_config = FitnessConfig()
    if data_config is None:
        data_config = DataConfig()
    
    # Use provided data loader or create mock data
    if data_loader is not None:
        if isinstance(data_loader, MockDataLoader):
            # Update seed based on consistent_data config
            # If consistent_data is True, use same seed across generations
            # If False, use seed + gen (different data per generation)
            consistent_data = getattr(data_config, 'consistent_data', True)
            if consistent_data:
                # Use base seed for consistent data across generations
                data_loader.seed = seed
            else:
                # Use seed + gen for varying data per generation (legacy behavior)
                data_loader.seed = seed + gen
        values, anomalies = data_loader.load()
        
        # Validate data loader output format
        assert isinstance(values, list), "values must be a list"
        assert isinstance(anomalies, list), "anomalies must be a list"
        assert len(values) == len(anomalies), "values and anomalies must have same length"
        assert all(isinstance(v, (int, float)) for v in values), "values must be numeric"
        assert all(isinstance(a, bool) for a in anomalies), "anomalies must be boolean"
    else:
        # Fallback to generate_mock_data for backward compatibility
        # Use consistent seed if configured, otherwise seed + gen
        consistent_data = getattr(data_config, 'consistent_data', True)
        data_seed = seed if consistent_data else seed + gen
        values, anomalies = generate_mock_data(
            data_seed,
            size=data_config.mock_size,
            anomaly_count=data_config.anomaly_count,
            anomaly_multiplier=data_config.anomaly_multiplier,
        )
    
    # HARD VALIDITY GATE: Check tree structure
    if not is_valid_alert_rule(tree):
        return -100.0
    
    tp = fp = fn = 0
    invalid_output_count = 0
    for idx, value in enumerate(values):
        window_size = 5 + (idx % 2)
        start = max(0, idx - window_size + 1)
        window = values[start : idx + 1]
        data = {"latency": window}
        result = evaluate(tree, data)
        
        # HARD VALIDITY GATE: Check output validity
        # Valid output is str (alert message) or None (no alert)
        if result is not None and not isinstance(result, str):
            invalid_output_count += 1
            # If we get invalid output, treat as no alert for this iteration
            result = None
        
        alerting = isinstance(result, str)
        if anomalies[idx] and alerting:
            tp += 1
        if anomalies[idx] and not alerting:
            fn += 1
        if not anomalies[idx] and alerting:
            fp += 1
    
    # Calculate metrics
    total_rows = len(values)
    alert_rate = (tp + fp) / total_rows if total_rows > 0 else 0.0
    invalid_rate = invalid_output_count / total_rows if total_rows > 0 else 0.0
    
    # HARD VALIDITY GATE: If too many invalid outputs, reject tree
    if invalid_rate > 0.5:  # More than 50% invalid outputs
        return -100.0
    
    # SOFT PENALTY: Penalize some invalid outputs (prefer robust trees)
    # This gives gradient pressure before hitting the 50% hard gate
    if invalid_rate > 0.0:
        score_invalid_penalty = 0.5 * invalid_rate  # Small penalty per invalid output
    else:
        score_invalid_penalty = 0.0
    
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
    
    # Apply invalid output penalty
    score -= score_invalid_penalty
    
    # NO-ALERT PENALTY: Trees that never alert are useless
    if tp == 0 and fp == 0:
        score -= 5.0  # Explicit penalty that dominates bloat incentives
    
    # ALERT-RATE BAND PENALTY: Prefer rules that alert at reasonable rates
    # Too low: < 0.2% (effectively never fires)
    # Too high: > 20% (too noisy)
    # Very high: > 50% ("always-true collapse" - must be strictly dominated)
    if alert_rate < 0.002:  # Less than 0.2%
        score -= 2.0  # Penalty for too-low alert rate
    elif alert_rate > 0.50:  # More than 50% - "always-true collapse"
        # Heavy penalty that scales with alert rate and dataset size
        # This ensures always-true rules are strictly dominated
        excess_rate = alert_rate - 0.5
        penalty = 2.0 * excess_rate * total_rows  # Scales with dataset size
        # For 100% alert rate on 1000 rows: penalty = 2.0 * 0.5 * 1000 = 1000 points
        score -= penalty
    elif alert_rate > 0.20:  # More than 20% but <= 50%
        score -= 3.0  # Penalty for too-high alert rate
    
    # MINIMUM TP FLOOR: Soft constraint for minimum useful detection
    # If we have labeled anomalies, require at least 1 TP (or recall >= 0.1)
    if possible_tp > 0:
        recall = tp / possible_tp
        if recall < 0.1 and tp == 0:  # No detection at all
            score -= 3.0  # Additional penalty for zero detection
    
    if fp > fitness_config.fp_threshold:
        score -= fitness_config.fp_penalty
    penalty = fitness_config.bloat_penalty * node_count(tree)
    return score - penalty


def baseline_always_false(
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> Dict[str, Any]:
    """Baseline: Rule that never alerts (always returns None)."""
    tree = ("if_alert", False, "Never alerts")
    return fitness_breakdown(tree, seed, gen, fitness_config, data_config, data_loader)


def baseline_always_true(
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> Dict[str, Any]:
    """Baseline: Rule that always alerts."""
    tree = ("if_alert", True, "Always alerts")
    return fitness_breakdown(tree, seed, gen, fitness_config, data_config, data_loader)


def baseline_random(
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
    threshold: float = 50.0,
) -> Dict[str, Any]:
    """Baseline: Simple rule comparing avg(latency) to threshold."""
    tree = ("if_alert", (">", ("avg", "latency"), threshold), "Random threshold")
    return fitness_breakdown(tree, seed, gen, fitness_config, data_config, data_loader)


def print_fitness_comparison(
    champion_tree: Any,
    champion_breakdown: Dict[str, Any],
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> None:
    """Print fitness breakdown comparing champion to baselines."""
    print("\n" + "=" * 70)
    print("  FITNESS BREAKDOWN COMPARISON")
    print("=" * 70)
    
    # Champion
    print(f"\nCHAMPION:")
    print(f"  Tree: {champion_tree}")
    print(f"  Fitness: {champion_breakdown['fitness']:.3f}")
    print(f"  TP: {champion_breakdown['tp']}, FP: {champion_breakdown['fp']}, FN: {champion_breakdown['fn']}")
    print(f"  TP Rate: {champion_breakdown['tp_rate']:.3f}, FP Rate: {champion_breakdown['fp_rate']:.3f}, FN Rate: {champion_breakdown['fn_rate']:.3f}")
    print(f"  F-beta: {champion_breakdown['f_beta']:.3f}")
    # New metrics
    alert_rate = champion_breakdown.get('alert_rate', 0.0)
    invalid_rate = champion_breakdown.get('invalid_rate', 0.0)
    node_count = champion_breakdown.get('node_count', 0)
    print(f"  Alert Rate: {alert_rate:.3f} ({alert_rate*100:.2f}%), Invalid Rate: {invalid_rate:.3f} ({invalid_rate*100:.2f}%)")
    print(f"  Node Count: {node_count}")
    
    # Baselines
    always_false = baseline_always_false(seed, gen, fitness_config, data_config, data_loader)
    always_true = baseline_always_true(seed, gen, fitness_config, data_config, data_loader)
    random_baseline = baseline_random(seed, gen, fitness_config, data_config, data_loader, threshold=50.0)
    
    print(f"\nBASELINES:")
    print(f"  Always-False: Fitness={always_false['fitness']:.3f}, TP={always_false['tp']}, FP={always_false['fp']}, FN={always_false['fn']}")
    print(f"  Always-True:  Fitness={always_true['fitness']:.3f}, TP={always_true['tp']}, FP={always_true['fp']}, FN={always_true['fn']}")
    print(f"  Random (avg>50): Fitness={random_baseline['fitness']:.3f}, TP={random_baseline['tp']}, FP={random_baseline['fp']}, FN={random_baseline['fn']}")
    
    # Comparison
    print(f"\nCHAMPION vs BASELINES:")
    improvement_over_false = champion_breakdown['fitness'] - always_false['fitness']
    improvement_over_true = champion_breakdown['fitness'] - always_true['fitness']
    improvement_over_random = champion_breakdown['fitness'] - random_baseline['fitness']
    
    print(f"  vs Always-False: {improvement_over_false:+.3f}")
    print(f"  vs Always-True:  {improvement_over_true:+.3f}")
    print(f"  vs Random:       {improvement_over_random:+.3f}")
    
    if champion_breakdown['fitness'] <= max(always_false['fitness'], always_true['fitness'], random_baseline['fitness']):
        print(f"\nWARNING: Champion is not better than all baselines!")
        print(f"   This suggests the evolution may be optimizing a loophole.")
    
    print("=" * 70 + "\n")

