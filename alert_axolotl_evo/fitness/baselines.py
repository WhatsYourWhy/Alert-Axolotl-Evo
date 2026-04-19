"""Degenerate-rule baselines and champion-vs-baseline comparison reporting.

A champion that does not strictly dominate all three baselines (always-false,
always-true, simple threshold) indicates an alignment loophole: the scoring
function is rewarding something other than real detection quality.
"""

from typing import Any, Dict, Optional

from alert_axolotl_evo.config import DataConfig, FitnessConfig
from alert_axolotl_evo.data import DataLoader
from alert_axolotl_evo.fitness.alignment import fitness_breakdown


class BaselineComparisonFailed(RuntimeError):
    """Raised when the evolved champion fails to beat all baselines.

    This is an alignment-invariant violation, not a runtime bug.
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


def baseline_always_false(
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> Dict[str, Any]:
    """Baseline: rule that never alerts."""
    tree = ("if_alert", False, "Never alerts")
    return fitness_breakdown(tree, seed, gen, fitness_config, data_config, data_loader)


def baseline_always_true(
    seed: int,
    gen: int,
    fitness_config: Optional[FitnessConfig] = None,
    data_config: Optional[DataConfig] = None,
    data_loader: Optional[DataLoader] = None,
) -> Dict[str, Any]:
    """Baseline: rule that always alerts."""
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
    """Baseline: simple avg(latency) > threshold rule."""
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
    """Print champion-vs-baselines comparison and return a structured result.

    Also verifies provenance: all baselines must be evaluated on the same
    dataset as the champion (same dataset_hash) for the comparison to be valid.
    """
    print("\n" + "=" * 70)
    print("  FITNESS BREAKDOWN COMPARISON")
    print("=" * 70)

    print("\nCHAMPION:")
    print(f"  Tree: {champion_tree}")
    print(f"  Fitness: {champion_breakdown['fitness']:.3f}")
    print(f"  TP: {champion_breakdown['tp']}, FP: {champion_breakdown['fp']}, FN: {champion_breakdown['fn']}")
    precision = champion_breakdown.get("precision", 0.0)
    fpr = champion_breakdown.get("fpr", 0.0)
    recall = champion_breakdown.get("recall", champion_breakdown.get("tp_rate", 0.0))
    print(f"  Recall: {recall:.3f} ({recall*100:.1f}%)")
    print(f"  Precision: {precision:.3f} ({precision*100:.1f}%)")
    print(f"  FPR: {fpr:.3f} ({fpr*100:.1f}%)")
    print(f"  F-beta: {champion_breakdown['f_beta']:.3f}")
    alert_rate = champion_breakdown.get("alert_rate", 0.0)
    invalid_rate = champion_breakdown.get("invalid_rate", 0.0)
    nodes = champion_breakdown.get("node_count", 0)
    print(f"  Alert Rate: {alert_rate:.3f} ({alert_rate*100:.2f}%), Invalid Rate: {invalid_rate:.3f} ({invalid_rate*100:.2f}%)")
    print(f"  Node Count: {nodes}")

    always_false = baseline_always_false(seed, gen, fitness_config, data_config, data_loader)
    always_true = baseline_always_true(seed, gen, fitness_config, data_config, data_loader)
    threshold = 50.0
    random_baseline = baseline_random(seed, gen, fitness_config, data_config, data_loader, threshold=threshold)

    champion_hash = champion_breakdown.get("data_provenance", {}).get("dataset_hash")
    baseline_hashes = [
        always_false.get("data_provenance", {}).get("dataset_hash"),
        always_true.get("data_provenance", {}).get("dataset_hash"),
        random_baseline.get("data_provenance", {}).get("dataset_hash"),
    ]

    provenance_ok = (
        champion_hash is not None
        and all(h == champion_hash for h in baseline_hashes if h is not None)
    )

    if not provenance_ok:
        print("\nWARNING: Dataset hash mismatch between champion and baselines!")
        print(f"  Champion hash: {champion_hash}")
        print(f"  Baseline hashes: {baseline_hashes}")
        print("  This indicates data mismatch - evidence is invalid.")

    print("\nBASELINES:")
    print(f"  Always-False: Fitness={always_false['fitness']:.3f}, TP={always_false['tp']}, FP={always_false['fp']}, FN={always_false['fn']}")
    print(f"  Always-True:  Fitness={always_true['fitness']:.3f}, TP={always_true['tp']}, FP={always_true['fp']}, FN={always_true['fn']}")
    print(f"  Random (avg>50): Fitness={random_baseline['fitness']:.3f}, TP={random_baseline['tp']}, FP={random_baseline['fp']}, FN={random_baseline['fn']}")

    print("\nCHAMPION vs BASELINES:")
    improvement_over_false = champion_breakdown["fitness"] - always_false["fitness"]
    improvement_over_true = champion_breakdown["fitness"] - always_true["fitness"]
    improvement_over_random = champion_breakdown["fitness"] - random_baseline["fitness"]
    print(f"  vs Always-False: {improvement_over_false:+.3f}")
    print(f"  vs Always-True:  {improvement_over_true:+.3f}")
    print(f"  vs Random:       {improvement_over_random:+.3f}")

    baseline_passed = champion_breakdown["fitness"] > max(
        always_false["fitness"],
        always_true["fitness"],
        random_baseline["fitness"],
    )

    if not baseline_passed:
        print("\nWARNING: Champion is not better than all baselines!")
        print("   This suggests the evolution may be optimizing a loophole.")

    print("=" * 70 + "\n")

    return {
        "baseline_passed": baseline_passed,
        "champion_breakdown": champion_breakdown,
        "baselines": {
            "always_false": always_false,
            "always_true": always_true,
            "random": random_baseline,
        },
        "comparison": {
            "vs_always_false": improvement_over_false,
            "vs_always_true": improvement_over_true,
            "vs_random": improvement_over_random,
        },
        "baseline_definitions": {
            "always_false": {"tree": ("if_alert", False, "Never alerts"), "threshold": None},
            "always_true": {"tree": ("if_alert", True, "Always alerts"), "threshold": None},
            "random": {
                "tree": ("if_alert", (">", ("avg", "latency"), threshold), "Random threshold"),
                "threshold": threshold,
            },
        },
        "provenance_ok": provenance_ok,
    }
