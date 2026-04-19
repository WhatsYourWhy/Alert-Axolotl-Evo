"""Operationally-aligned fitness scoring.

This module implements the scoring pipeline that ties fitness to deployment
constraints — precision floors, FPR ceilings, alert-rate bands, recall floors,
and degenerate-rule detection. See docs/fitness-alignment.md for the rationale
behind each threshold.

`fitness_breakdown` returns the full metric dictionary (used for debugging,
baseline comparison, and provenance). `fitness` returns a scalar and is the
hot path called from the evolution loop.
"""

import hashlib
import json
from typing import Any, Dict, Optional

from alert_axolotl_evo.config import DataConfig, FitnessConfig
from alert_axolotl_evo.data import DataLoader, MockDataLoader
from alert_axolotl_evo.fitness.evaluator import evaluate, generate_mock_data
from alert_axolotl_evo.tree import is_self_comparison, is_valid_alert_rule, node_count


def _load_or_mock(
    seed: int,
    gen: int,
    data_config: DataConfig,
    data_loader: Optional[DataLoader],
):
    """Resolve (values, anomalies) from a data loader or fall back to mock data."""
    if data_loader is not None:
        if isinstance(data_loader, MockDataLoader):
            consistent_data = getattr(data_config, "consistent_data", True)
            data_loader.seed = seed if consistent_data else seed + gen
        values, anomalies = data_loader.load()
        assert isinstance(values, list), "values must be a list"
        assert isinstance(anomalies, list), "anomalies must be a list"
        assert len(values) == len(anomalies), "values and anomalies must have same length"
        assert all(isinstance(v, (int, float)) for v in values), "values must be numeric"
        assert all(isinstance(a, bool) for a in anomalies), "anomalies must be boolean"
        return values, anomalies

    consistent_data = getattr(data_config, "consistent_data", True)
    data_seed = seed if consistent_data else seed + gen
    return generate_mock_data(
        data_seed,
        size=data_config.mock_size,
        anomaly_count=data_config.anomaly_count,
        anomaly_multiplier=data_config.anomaly_multiplier,
    )


def fitness_breakdown(
    tree: Any,
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> Dict[str, Any]:
    """Compute fitness and return the full metric/provenance breakdown.

    Use this (not `fitness`) when you need precision, FPR, recall, alert rate,
    invalid rate, dataset hash, or exception counts — e.g. for logging or
    baseline comparison.
    """
    if fitness_config is None:
        fitness_config = FitnessConfig()
    if data_config is None:
        data_config = DataConfig()

    values, anomalies = _load_or_mock(seed, gen, data_config, data_loader)

    tp = fp = fn = 0
    invalid_output_count = 0
    exception_count = 0
    total_rows = len(values)

    # Stratified early rejection: sample 5% head and 5% tail. Window-based
    # trees can pass the head but fail the tail once a window fills.
    sample_size = max(10, total_rows // 20)
    early_slice_end = min(sample_size, total_rows)
    late_slice_start = max(0, total_rows - sample_size)
    early_rejected = False
    early_invalid_count = 0
    late_invalid_count = 0

    idx = -1
    for idx, value in enumerate(values):
        window_size = 5 + (idx % 2)
        start = max(0, idx - window_size + 1)
        window = values[start : idx + 1]
        data = {"latency": window}

        try:
            result = evaluate(tree, data)
        except Exception:
            exception_count += 1
            result = None

        is_invalid = False
        if isinstance(result, tuple) and len(result) > 0:
            if result[0] in ("__INVALID_CONDITION__", "__INVALID_MESSAGE__"):
                invalid_output_count += 1
                is_invalid = True
                result = None
            elif result is not None and not isinstance(result, str):
                invalid_output_count += 1
                is_invalid = True
                result = None
        elif result is not None and not isinstance(result, str):
            invalid_output_count += 1
            is_invalid = True
            result = None

        if is_invalid:
            if idx < early_slice_end:
                early_invalid_count += 1
            if idx >= late_slice_start:
                late_invalid_count += 1

        alerting = isinstance(result, str)
        if anomalies[idx] and alerting:
            tp += 1
        if anomalies[idx] and not alerting:
            fn += 1
        if not anomalies[idx] and alerting:
            fp += 1

        if idx + 1 == early_slice_end and not early_rejected:
            early_invalid_rate = early_invalid_count / early_slice_end if early_slice_end > 0 else 0.0
            if early_invalid_rate > 0.5:
                early_rejected = True
                break

        if idx + 1 == late_slice_start + sample_size and not early_rejected:
            late_invalid_rate = late_invalid_count / sample_size if sample_size > 0 else 0.0
            if late_invalid_rate > 0.5:
                early_rejected = True
                break

    evaluated_rows = idx + 1 if early_rejected else total_rows
    alert_rate = (tp + fp) / evaluated_rows if evaluated_rows > 0 else 0.0
    invalid_rate = invalid_output_count / evaluated_rows if evaluated_rows > 0 else 0.0
    exception_rate = exception_count / evaluated_rows if evaluated_rows > 0 else 0.0
    invalid_evaluation = invalid_rate > 0.5

    if early_rejected:
        evaluated_anomalies = anomalies[:evaluated_rows] if anomalies else []
        possible_tp = sum(evaluated_anomalies) if evaluated_anomalies else 0
    else:
        possible_tp = sum(anomalies) if anomalies else data_config.anomaly_count
    normal_count = evaluated_rows - possible_tp
    tp_rate = tp / possible_tp if possible_tp > 0 else 0.0
    fp_rate = fp / possible_tp if possible_tp > 0 else 0.0
    fn_rate = fn / possible_tp if possible_tp > 0 else 0.0

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    fpr = fp / normal_count if normal_count > 0 else 0.0
    recall = tp_rate

    beta = fitness_config.beta
    beta_sq = beta**2
    denom = (1 + beta_sq) * tp_rate + beta_sq * fn_rate + fp_rate
    f_beta = ((1 + beta_sq) * tp_rate / denom) if denom else 0.0
    score = f_beta * possible_tp

    if invalid_rate > 0.0:
        score -= 0.5 * invalid_rate

    if isinstance(tree, tuple) and len(tree) >= 3 and tree[0] == "if_alert":
        if is_self_comparison(tree[1]):
            score -= 10.0

    if tp == 0 and fp == 0:
        score -= 5.0

    if alert_rate < 0.002:
        score -= 2.0
    elif alert_rate > 0.50:
        excess_rate = alert_rate - 0.5
        score -= 2.0 * excess_rate * total_rows
    elif alert_rate > 0.20:
        score -= 3.0

    if possible_tp > 0:
        recall = tp / possible_tp
        if recall < 0.1 and tp == 0:
            score -= 3.0

    if fp > fitness_config.fp_threshold:
        score -= fitness_config.fp_penalty
    penalty = fitness_config.bloat_penalty * node_count(tree)
    final_fitness = score - penalty

    consistent_data = getattr(data_config, "consistent_data", True)

    values_rounded = [round(v, 6) for v in values]
    dataset_content = {"values": values_rounded, "anomalies": anomalies}
    dataset_json = json.dumps(dataset_content, sort_keys=True)
    dataset_hash = hashlib.sha256(dataset_json.encode()).hexdigest()[:16]

    data_provenance = {
        "seed": seed,
        "gen": gen,
        "consistent_data": consistent_data,
        "data_loader_type": type(data_loader).__name__ if data_loader else "mock",
        "mock_size": data_config.mock_size,
        "anomaly_count": data_config.anomaly_count,
        "anomaly_multiplier": data_config.anomaly_multiplier,
        "use_realistic_patterns": getattr(data_loader, "use_realistic_patterns", None) if data_loader else None,
        "base_latency_mean": getattr(data_loader, "base_latency_mean", None) if data_loader else None,
        "base_latency_std": getattr(data_loader, "base_latency_std", None) if data_loader else None,
        "trend_strength": getattr(data_loader, "trend_strength", None) if data_loader else None,
        "noise_level": getattr(data_loader, "noise_level", None) if data_loader else None,
        "data_path": str(data_config.data_path) if data_config.data_path else None,
        "data_source": data_config.data_source,
        "dataset_hash": dataset_hash,
    }

    if data_config.data_path and data_config.data_path.exists():
        stat = data_config.data_path.stat()
        data_provenance["file_mtime"] = stat.st_mtime
        data_provenance["file_size"] = stat.st_size

    return {
        "fitness": final_fitness,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "possible_tp": possible_tp,
        "normal_count": normal_count,
        "tp_rate": tp_rate,
        "fp_rate": fp_rate,
        "fn_rate": fn_rate,
        "precision": precision,
        "fpr": fpr,
        "recall": recall,
        "f_beta": f_beta,
        "score": score,
        "penalty": penalty,
        "alert_rate": alert_rate,
        "invalid_rate": invalid_rate,
        "node_count": node_count(tree),
        "exception_rate": exception_rate,
        "invalid_evaluation": invalid_evaluation,
        "data_provenance": data_provenance,
    }


def fitness(
    tree: Any,
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> float:
    """Compute the scalar fitness score for a tree.

    This is the hot path called from the evolution loop. For diagnostic
    components (precision, FPR, alert rate, etc.) call `fitness_breakdown`.

    Must remain pure — no global state mutation, no learning side effects.
    """
    if fitness_config is None:
        fitness_config = FitnessConfig()
    if data_config is None:
        data_config = DataConfig()

    values, anomalies = _load_or_mock(seed, gen, data_config, data_loader)

    if not is_valid_alert_rule(tree):
        return -100.0

    tp = fp = fn = 0
    invalid_output_count = 0
    total_rows = len(values)

    sample_size = max(10, total_rows // 20)
    early_slice_end = min(sample_size, total_rows)
    late_slice_start = max(0, total_rows - sample_size)
    early_rejection_checked = False

    for idx, value in enumerate(values):
        window_size = 5 + (idx % 2)
        start = max(0, idx - window_size + 1)
        window = values[start : idx + 1]
        data = {"latency": window}
        result = evaluate(tree, data)

        if isinstance(result, tuple) and len(result) > 0:
            if result[0] in ("__INVALID_CONDITION__", "__INVALID_MESSAGE__"):
                invalid_output_count += 1
                result = None
            elif result is not None and not isinstance(result, str):
                invalid_output_count += 1
                result = None
        elif result is not None and not isinstance(result, str):
            invalid_output_count += 1
            result = None

        alerting = isinstance(result, str)
        if anomalies[idx] and alerting:
            tp += 1
        if anomalies[idx] and not alerting:
            fn += 1
        if not anomalies[idx] and alerting:
            fp += 1

        if not early_rejection_checked:
            if idx + 1 >= early_slice_end:
                early_invalid_rate = invalid_output_count / (idx + 1)
                if early_invalid_rate > 0.5:
                    return -100.0
            elif idx + 1 >= late_slice_start:
                if idx + 1 >= total_rows:
                    early_rejection_checked = True
                    overall_invalid_rate = invalid_output_count / total_rows
                    if overall_invalid_rate > 0.5:
                        return -100.0

    alert_rate = (tp + fp) / total_rows if total_rows > 0 else 0.0
    invalid_rate = invalid_output_count / total_rows if total_rows > 0 else 0.0

    if invalid_rate > 0.5:
        return -100.0

    score_invalid_penalty = 0.5 * invalid_rate if invalid_rate > 0.0 else 0.0

    possible_tp = sum(anomalies) if anomalies else data_config.anomaly_count
    tp_rate = tp / possible_tp if possible_tp > 0 else 0.0
    fp_rate = fp / possible_tp if possible_tp > 0 else 0.0
    fn_rate = fn / possible_tp if possible_tp > 0 else 0.0
    beta = fitness_config.beta
    beta_sq = beta**2
    denom = (1 + beta_sq) * tp_rate + beta_sq * fn_rate + fp_rate
    f_beta = ((1 + beta_sq) * tp_rate / denom) if denom else 0.0
    score = f_beta * possible_tp - score_invalid_penalty

    # Degenerate-collapse prevention: self-comparisons and no-alert rules.
    if isinstance(tree, tuple) and len(tree) >= 3 and tree[0] == "if_alert":
        if is_self_comparison(tree[1]):
            score -= 10.0
    if tp == 0 and fp == 0:
        score -= 5.0

    # Alert-rate band: 0.2% floor, 20% ceiling, 50% hard collapse.
    # Above 50% the penalty scales with dataset size so always-true rules
    # are strictly dominated.
    if alert_rate < 0.002:
        score -= 2.0
    elif alert_rate > 0.50:
        excess_rate = alert_rate - 0.5
        score -= 2.0 * excess_rate * total_rows
    elif alert_rate > 0.20:
        score -= 3.0

    normal_count = total_rows - possible_tp
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    fpr = fp / normal_count if normal_count > 0 else 0.0
    recall = tp / possible_tp if possible_tp > 0 else 0.0

    # Precision pressure: target >= 30% for human-paged alerts.
    if (tp + fp) > 0 and precision < 0.3:
        score -= 5.0 * (0.3 - precision)

    # FPR ceiling: 15% operational noise tolerance.
    if fpr > 0.15:
        score -= 2.0 * (fpr - 0.15)

    # Recall floor: at least some detection required.
    if possible_tp > 0 and recall < 0.1 and tp == 0:
        score -= 3.0

    if fp > fitness_config.fp_threshold:
        score -= fitness_config.fp_penalty
    penalty = fitness_config.bloat_penalty * node_count(tree)
    return score - penalty
