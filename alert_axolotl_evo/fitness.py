"""
Fitness evaluation and tree evaluation.

This module implements Metric-Aligned Semantic Program Synthesis, where fitness
scores are aligned with real-world operational constraints rather than simply
optimized for higher numbers. This ensures that "high fitness" means "operationally
useful" - meeting precision requirements, staying within false positive limits,
and functioning within deployment constraints.

Key Alignment Mechanisms:
- Precision pressure (≥30% for human-paged alerts)
- FPR penalties (≤15% operational noise tolerance)
- Alert-rate bands (0.2%-20% deployment feasibility)
- Recall floors (≥10% minimum usefulness)
- Degenerate collapse prevention (always-true/always-false elimination)
- Invalid output gates (semantic error detection)

See docs/FITNESS_ALIGNMENT.md for comprehensive documentation.
"""

import random
from typing import Any, Callable, Dict, List, Optional, Tuple

from alert_axolotl_evo.config import DataConfig, FitnessConfig
from alert_axolotl_evo.data import DataLoader, MockDataLoader
from alert_axolotl_evo.primitives import ALERT, FUNCTIONS, ARITIES
from alert_axolotl_evo.tree import is_valid_alert_rule, node_count, is_self_comparison


class BaselineComparisonFailed(RuntimeError):
    """
    Raised when evolved champion fails to beat baseline comparisons.
    
    This is a fitness invariant violation, not a runtime bug. It indicates
    that alignment may be broken or evolution found a loophole.
    
    Attributes:
        champion_breakdown: Fitness breakdown of the champion
        baselines: Dictionary of baseline breakdowns
        message: Human-readable error message
    """
    def __init__(
        self,
        message: str,
        champion_breakdown: Dict[str, Any],
        baselines: Dict[str, Dict[str, Any]],
    ):
        super().__init__(message)
        self.champion_breakdown = champion_breakdown
        self.baselines = baselines


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
    # For invalid conditions, returns a special sentinel tuple to mark invalidity
    if op == "if_alert":
        if len(tree) != 3:
            return None
        cond_val = _evaluate(tree[1], data)
        msg = _evaluate(tree[2], data)
        
        # STRICT: condition must be bool, not truthy
        # This prevents strings/numbers from being "always true"
        if type(cond_val) is not bool:
            # Return a special sentinel to mark invalid condition
            # This will be detected in fitness evaluation and counted as invalid
            return ("__INVALID_CONDITION__", cond_val, msg)
        
        # Message must be a string
        if not isinstance(msg, str):
            # Return a special sentinel to mark invalid message
            return ("__INVALID_MESSAGE__", cond_val, msg)
        
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
    
    This function provides a detailed breakdown of fitness components, including
    all alignment metrics (precision, FPR, alert rate, recall, etc.). Useful for
    understanding why a rule has a particular fitness score and verifying that
    alignment mechanisms are working correctly.
    
    See docs/FITNESS_ALIGNMENT.md for documentation of alignment mechanisms.
    
    Args:
        tree: The evolved rule tree to evaluate
        seed: Random seed for data generation
        gen: Generation number (affects data if consistent_data=False)
        fitness_config: Fitness configuration parameters
        data_config: Data configuration parameters
        data_loader: Optional data loader (overrides data_config)
    
    Returns:
        Dictionary with keys:
        - fitness: Final fitness score (after all penalties)
        - tp, fp, fn: True positives, false positives, false negatives
        - possible_tp, normal_count: Total anomalies and normal samples
        - tp_rate, fp_rate, fn_rate: Rates relative to possible_tp
        - precision: TP/(TP+FP) - classic precision metric
        - fpr: FP/normal_count - classic false positive rate
        - recall: TP/possible_tp - alias for tp_rate
        - f_beta: F-beta score (before penalties)
        - score: Base score (f_beta * possible_tp, before penalties)
        - penalty: Bloat penalty (node_count * bloat_penalty)
        - alert_rate: (TP+FP)/total_rows - overall alert rate
        - invalid_rate: Rate of invalid outputs
        - node_count: Tree size (for parsimony)
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
    eval_error_occurred = False
    for idx, value in enumerate(values):
        window_size = 5 + (idx % 2)
        start = max(0, idx - window_size + 1)
        window = values[start : idx + 1]
        data = {"latency": window}
        
        try:
            result = evaluate(tree, data)
        except Exception:
            # Eval error occurred - mark evidence as invalid
            eval_error_occurred = True
            result = None
        
        # HARD VALIDITY GATE: Check output validity
        # Valid output is str (alert message) or None (no alert)
        # Invalid conditions/messages return special sentinel tuples
        if isinstance(result, tuple) and len(result) > 0:
            if result[0] in ("__INVALID_CONDITION__", "__INVALID_MESSAGE__"):
                invalid_output_count += 1
                # Treat as no alert for this iteration
                result = None
            elif result is not None and not isinstance(result, str):
                invalid_output_count += 1
                result = None
        elif result is not None and not isinstance(result, str):
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
    normal_count = total_rows - possible_tp
    tp_rate = tp / possible_tp if possible_tp > 0 else 0.0
    fp_rate = fp / possible_tp if possible_tp > 0 else 0.0  # Domain metric: FP per anomaly
    fn_rate = fn / possible_tp if possible_tp > 0 else 0.0
    
    # Calculate classic metrics for precision pressure
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    fpr = fp / normal_count if normal_count > 0 else 0.0  # Classic FPR: FP / normal_count
    recall = tp_rate  # Alias for clarity
    
    beta = fitness_config.beta
    beta_sq = beta**2
    denom = (1 + beta_sq) * tp_rate + beta_sq * fn_rate + fp_rate
    f_beta = ((1 + beta_sq) * tp_rate / denom) if denom else 0.0
    score = f_beta * possible_tp
    
    # SOFT PENALTY: Penalize invalid outputs
    if invalid_rate > 0.0:
        score -= 0.5 * invalid_rate
    
    # DEGENERATE COMPARISON PENALTY: Self-comparisons are always False/True and useless
    # Check the condition subtree for self-comparisons
    if isinstance(tree, tuple) and len(tree) >= 3 and tree[0] == "if_alert":
        condition = tree[1]
        if is_self_comparison(condition):
            score -= 10.0  # Heavy penalty for self-comparisons (always False/True)
    
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
    
    # Determine consistent_data flag for provenance
    consistent_data = getattr(data_config, 'consistent_data', True)
    
    return {
        "fitness": final_fitness,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "possible_tp": possible_tp,
        "normal_count": normal_count,
        "tp_rate": tp_rate,
        "fp_rate": fp_rate,  # Domain metric: FP per anomaly
        "fn_rate": fn_rate,
        "precision": precision,  # Classic: TP/(TP+FP)
        "fpr": fpr,  # Classic: FP/normal_count
        "recall": recall,  # Alias for tp_rate
        "f_beta": f_beta,
        "score": score,
        "penalty": penalty,
        "alert_rate": alert_rate,
        "invalid_rate": invalid_rate,
        "node_count": node_count(tree),
        "eval_error": eval_error_occurred,
        "data_provenance": {
            "seed": seed,
            "gen": gen,
            "consistent_data": consistent_data,
            "data_loader_type": type(data_loader).__name__ if data_loader else "mock",
        },
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
    
    This function implements Metric-Aligned Semantic Program Synthesis, where
    fitness scores are aligned with operational constraints:
    - Precision pressure (≥30% for human-paged alerts)
    - FPR penalties (≤15% operational noise tolerance)
    - Alert-rate bands (0.2%-20% deployment feasibility)
    - Recall floors (≥10% minimum usefulness)
    - Degenerate collapse prevention (always-true/always-false elimination)
    
    NOTE: fitness must be pure and side-effect free.
    This function computes a score based on tree evaluation and data.
    It does not modify global state, registries, or learning mechanisms.
    
    See docs/FITNESS_ALIGNMENT.md for comprehensive documentation of alignment
    mechanisms and their operational justifications.
    
    Args:
        tree: The evolved rule tree to evaluate
        seed: Random seed for data generation
        gen: Generation number (affects data if consistent_data=False)
        fitness_config: Fitness configuration parameters
        data_config: Data configuration parameters
        data_loader: Optional data loader (overrides data_config)
    
    Returns:
        Fitness score (higher is better, but must meet operational constraints)
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
        # Invalid conditions/messages return special sentinel tuples
        if isinstance(result, tuple) and len(result) > 0:
            if result[0] in ("__INVALID_CONDITION__", "__INVALID_MESSAGE__"):
                invalid_output_count += 1
                # Treat as no alert for this iteration
                result = None
            elif result is not None and not isinstance(result, str):
                invalid_output_count += 1
                result = None
        elif result is not None and not isinstance(result, str):
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
    
    # ============================================================================
    # FITNESS ALIGNMENT: Operational Constraints
    # ============================================================================
    # This section implements Metric-Aligned Semantic Program Synthesis.
    # Each penalty maps to an operational constraint, not just a tuning parameter.
    # See docs/FITNESS_ALIGNMENT.md for comprehensive documentation.
    # ============================================================================
    
    # ----------------------------------------------------------------------------
    # Degenerate Collapse Prevention
    # ----------------------------------------------------------------------------
    # Operational Constraint: Rules that always return True or always return False
    # are useless, even if they technically have "good" metrics.
    #
    # Self-Comparison Detection: Self-comparisons (e.g., x > x) always evaluate
    # to False/True and provide no useful logic.
    #
    # No-Alert Detection: Rules that never alert (tp=0, fp=0) are useless even
    # if they avoid false positives.
    # ----------------------------------------------------------------------------
    
    # DEGENERATE COMPARISON PENALTY: Self-comparisons are always False/True and useless
    # Check the condition subtree for self-comparisons
    if isinstance(tree, tuple) and len(tree) >= 3 and tree[0] == "if_alert":
        condition = tree[1]
        if is_self_comparison(condition):
            score -= 10.0  # Heavy penalty for self-comparisons (always False/True)
    
    # NO-ALERT PENALTY: Trees that never alert are useless
    if tp == 0 and fp == 0:
        score -= 5.0  # Explicit penalty that dominates bloat incentives
    
    # ----------------------------------------------------------------------------
    # Alert-Rate Band Constraints
    # ----------------------------------------------------------------------------
    # Operational Constraint: Rules must alert at deployment-feasible rates.
    # Too low (<0.2%): Never fires (useless)
    # Too high (>20%): Too noisy (operational fatigue)
    # Very high (>50%): "Always-true collapse" (must be strictly dominated)
    #
    # Thresholds:
    # - 0.2% floor: Rules below this are effectively never-firing
    # - 20% ceiling: Rules above this become too noisy for operational use
    # - 50% hard limit: Above this, rules are "always-true" and must be strictly
    #   dominated (penalty scales with dataset size to ensure dominance)
    # ----------------------------------------------------------------------------
    
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
    
    # ----------------------------------------------------------------------------
    # Precision Pressure
    # ----------------------------------------------------------------------------
    # Operational Constraint: Human-paged alerts have real cost. If precision is
    # too low, operators get overwhelmed by false alarms.
    #
    # Threshold: 30% precision minimum
    # Justification: This represents a reasonable balance for human-paged alerts.
    # Below this, the operational cost of false alarms exceeds the value of detection.
    #
    # Penalty: Scales with precision deficit (max 1.5 points for 0% precision)
    # ----------------------------------------------------------------------------
    
    # PRECISION PRESSURE: Penalize low precision (too many false alarms)
    # Target precision >= 0.3 (30%) for human-paged alerts
    normal_count = total_rows - possible_tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    fpr = fp / normal_count if normal_count > 0 else 0.0
    recall = tp / possible_tp if possible_tp > 0 else 0.0
    
    if (tp + fp) > 0:
        if precision < 0.3:
            # Soft penalty that scales with how far below target
            precision_deficit = 0.3 - precision
            score -= 5.0 * precision_deficit  # Max penalty of 1.5 for 0% precision
    
    # ----------------------------------------------------------------------------
    # FPR Penalties
    # ----------------------------------------------------------------------------
    # Operational Constraint: False positive rate must stay within operational
    # noise tolerance. High FPR creates alert fatigue.
    #
    # Threshold: 15% FPR maximum
    # Justification: This represents the maximum acceptable false positive rate
    # for operational monitoring. Beyond this, alert fatigue sets in and operators
    # start ignoring alerts.
    #
    # Penalty: Scales with excess FPR (2.0 * (fpr - 0.15))
    # ----------------------------------------------------------------------------
    
    # FPR PENALTY: Also penalize very high false positive rate directly
    if fpr > 0.15:  # More than 15% false positive rate
        score -= 2.0 * (fpr - 0.15)  # Penalty scales with excess FPR
    
    # ----------------------------------------------------------------------------
    # Recall Floors
    # ----------------------------------------------------------------------------
    # Operational Constraint: Rules must detect at least some anomalies to be
    # useful. Zero detection is worse than useless.
    #
    # Threshold: 10% recall minimum (or at least 1 TP)
    # Justification: This ensures rules have minimum useful detection. Rules with
    # zero true positives are explicitly penalized.
    #
    # Penalty: 3.0 points for zero detection (recall < 0.1 and tp == 0)
    # ----------------------------------------------------------------------------
    
    # MINIMUM TP FLOOR: Soft constraint for minimum useful detection
    # If we have labeled anomalies, require at least 1 TP (or recall >= 0.1)
    if possible_tp > 0:
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
) -> Dict[str, Any]:
    """
    Print fitness breakdown comparing champion to baselines.
    
    This function validates fitness alignment by comparing the evolved champion
    against three degenerate baselines:
    1. Always-False: Rule that never alerts
    2. Always-True: Rule that always alerts
    3. Random Baseline: Simple threshold rule
    
    If alignment is working correctly, the champion should strictly dominate all
    baselines. If not, this indicates a loophole in the alignment mechanisms.
    
    This is a critical sanity check for fitness alignment. See
    docs/FITNESS_ALIGNMENT.md for more on baseline verification.
    
    Args:
        champion_tree: The evolved champion rule
        champion_breakdown: Fitness breakdown from fitness_breakdown()
        seed: Random seed for baseline evaluation
        gen: Generation number
        fitness_config: Fitness configuration
        data_config: Data configuration
        data_loader: Optional data loader
    
    Returns:
        Dictionary with:
        - 'baseline_passed': bool
        - 'champion_breakdown': Dict
        - 'baselines': Dict[str, Dict] with keys 'always_false', 'always_true', 'random'
        - 'comparison': Dict with improvement deltas
        - 'baseline_definitions': Dict with baseline tree definitions
    """
    print("\n" + "=" * 70)
    print("  FITNESS BREAKDOWN COMPARISON")
    print("=" * 70)
    
    # Champion
    print(f"\nCHAMPION:")
    print(f"  Tree: {champion_tree}")
    print(f"  Fitness: {champion_breakdown['fitness']:.3f}")
    print(f"  TP: {champion_breakdown['tp']}, FP: {champion_breakdown['fp']}, FN: {champion_breakdown['fn']}")
    # Classic metrics
    precision = champion_breakdown.get('precision', 0.0)
    fpr = champion_breakdown.get('fpr', 0.0)
    recall = champion_breakdown.get('recall', champion_breakdown.get('tp_rate', 0.0))
    print(f"  Recall: {recall:.3f} ({recall*100:.1f}%)")
    print(f"  Precision: {precision:.3f} ({precision*100:.1f}%)")
    print(f"  FPR: {fpr:.3f} ({fpr*100:.1f}%)")
    print(f"  F-beta: {champion_breakdown['f_beta']:.3f}")
    # Additional metrics
    alert_rate = champion_breakdown.get('alert_rate', 0.0)
    invalid_rate = champion_breakdown.get('invalid_rate', 0.0)
    node_count = champion_breakdown.get('node_count', 0)
    print(f"  Alert Rate: {alert_rate:.3f} ({alert_rate*100:.2f}%), Invalid Rate: {invalid_rate:.3f} ({invalid_rate*100:.2f}%)")
    print(f"  Node Count: {node_count}")
    
    # Baselines
    always_false = baseline_always_false(seed, gen, fitness_config, data_config, data_loader)
    always_true = baseline_always_true(seed, gen, fitness_config, data_config, data_loader)
    threshold = 50.0  # Default threshold for random baseline
    random_baseline = baseline_random(seed, gen, fitness_config, data_config, data_loader, threshold=threshold)
    
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
    
    baseline_passed = champion_breakdown['fitness'] > max(
        always_false['fitness'], 
        always_true['fitness'], 
        random_baseline['fitness']
    )
    
    if not baseline_passed:
        print(f"\nWARNING: Champion is not better than all baselines!")
        print(f"   This suggests the evolution may be optimizing a loophole.")
    
    print("=" * 70 + "\n")
    
    # Return structured comparison result
    comparison_result = {
        'baseline_passed': baseline_passed,
        'champion_breakdown': champion_breakdown,
        'baselines': {
            'always_false': always_false,
            'always_true': always_true,
            'random': random_baseline,
        },
        'comparison': {
            'vs_always_false': improvement_over_false,
            'vs_always_true': improvement_over_true,
            'vs_random': improvement_over_random,
        },
        'baseline_definitions': {
            'always_false': {'tree': ("if_alert", False, "Never alerts"), 'threshold': None},
            'always_true': {'tree': ("if_alert", True, "Always alerts"), 'threshold': None},
            'random': {
                'tree': ("if_alert", (">", ("avg", "latency"), threshold), "Random threshold"),
                'threshold': threshold,
            },
        },
    }
    
    return comparison_result

