"""
Fitness Alignment Demonstration

This script demonstrates fitness alignment mechanisms in action, showing how
alignment ensures that "high fitness" means "operationally useful" rather than
just "numerically high".

See docs/FITNESS_ALIGNMENT.md for comprehensive documentation.
"""

from alert_axolotl_evo.fitness import (
    fitness_breakdown,
    print_fitness_comparison,
    baseline_always_false,
    baseline_always_true,
    baseline_random,
)
from alert_axolotl_evo.config import Config


def demonstrate_precision_pressure():
    """Demonstrate precision pressure mechanism."""
    print("\n" + "=" * 70)
    print("PRECISION PRESSURE DEMONSTRATION")
    print("=" * 70)
    
    # Rule with low threshold (many false positives, low precision)
    low_precision_tree = ("if_alert", (">", ("avg", "latency"), 10), "Low threshold")
    breakdown = fitness_breakdown(low_precision_tree, seed=42, gen=0)
    
    print(f"\nRule: {low_precision_tree}")
    print(f"Precision: {breakdown['precision']:.3f} ({breakdown['precision']*100:.1f}%)")
    print(f"FPR: {breakdown['fpr']:.3f} ({breakdown['fpr']*100:.1f}%)")
    print(f"TP: {breakdown['tp']}, FP: {breakdown['fp']}, FN: {breakdown['fn']}")
    print(f"Base Score: {breakdown['score']:.3f}")
    print(f"Final Fitness: {breakdown['fitness']:.3f}")
    
    if breakdown['precision'] < 0.3:
        penalty = breakdown['score'] - breakdown['fitness']
        print(f"\n⚠️  Precision below 30% threshold!")
        print(f"   Penalty applied: {penalty:.3f} points")
        print(f"   Operational impact: Too many false alarms for human-paged alerts")
    else:
        print(f"\n✓ Precision meets 30% threshold")


def demonstrate_fpr_penalty():
    """Demonstrate FPR penalty mechanism."""
    print("\n" + "=" * 70)
    print("FPR PENALTY DEMONSTRATION")
    print("=" * 70)
    
    # Rule with very low threshold (high false positive rate)
    high_fpr_tree = ("if_alert", (">", ("avg", "latency"), 5), "Very low threshold")
    breakdown = fitness_breakdown(high_fpr_tree, seed=42, gen=0)
    
    print(f"\nRule: {high_fpr_tree}")
    print(f"FPR: {breakdown['fpr']:.3f} ({breakdown['fpr']*100:.1f}%)")
    print(f"Precision: {breakdown['precision']:.3f} ({breakdown['precision']*100:.1f}%)")
    print(f"TP: {breakdown['tp']}, FP: {breakdown['fp']}, FN: {breakdown['fn']}")
    print(f"Base Score: {breakdown['score']:.3f}")
    print(f"Final Fitness: {breakdown['fitness']:.3f}")
    
    if breakdown['fpr'] > 0.15:
        penalty = breakdown['score'] - breakdown['fitness']
        print(f"\n⚠️  FPR above 15% threshold!")
        print(f"   Penalty applied: {penalty:.3f} points")
        print(f"   Operational impact: Alert fatigue - operators start ignoring alerts")
    else:
        print(f"\n✓ FPR within 15% threshold")


def demonstrate_alert_rate_bands():
    """Demonstrate alert-rate band constraints."""
    print("\n" + "=" * 70)
    print("ALERT-RATE BAND DEMONSTRATION")
    print("=" * 70)
    
    # Test three scenarios: too low, acceptable, too high
    scenarios = [
        ("Too Low", ("if_alert", (">", ("max", "latency"), 10000), "Very high threshold")),
        ("Acceptable", ("if_alert", (">", ("max", "latency"), 75), "Reasonable threshold")),
        ("Too High", ("if_alert", True, "Always alerts")),
    ]
    
    for name, tree in scenarios:
        breakdown = fitness_breakdown(tree, seed=42, gen=0)
        alert_rate_pct = breakdown['alert_rate'] * 100
        
        print(f"\n{name}:")
        print(f"  Rule: {tree}")
        print(f"  Alert Rate: {breakdown['alert_rate']:.3f} ({alert_rate_pct:.2f}%)")
        print(f"  Base Score: {breakdown['score']:.3f}")
        print(f"  Final Fitness: {breakdown['fitness']:.3f}")
        
        if breakdown['alert_rate'] < 0.002:
            print(f"  ⚠️  Too low (<0.2%) - effectively never fires")
        elif breakdown['alert_rate'] > 0.50:
            print(f"  ⚠️  Too high (>50%) - 'always-true collapse', heavy penalty")
        elif breakdown['alert_rate'] > 0.20:
            print(f"  ⚠️  Too high (>20%) - too noisy for operational use")
        else:
            print(f"  ✓ Within acceptable range (0.2%-20%)")


def demonstrate_recall_floor():
    """Demonstrate recall floor constraint."""
    print("\n" + "=" * 70)
    print("RECALL FLOOR DEMONSTRATION")
    print("=" * 70)
    
    # Rule that never detects anomalies
    never_detects_tree = ("if_alert", (">", ("max", "latency"), 10000), "Too high")
    breakdown = fitness_breakdown(never_detects_tree, seed=42, gen=0)
    
    print(f"\nRule: {never_detects_tree}")
    print(f"Recall: {breakdown['recall']:.3f} ({breakdown['recall']*100:.1f}%)")
    print(f"TP: {breakdown['tp']}, FP: {breakdown['fp']}, FN: {breakdown['fn']}")
    print(f"Base Score: {breakdown['score']:.3f}")
    print(f"Final Fitness: {breakdown['fitness']:.3f}")
    
    if breakdown['recall'] < 0.1 and breakdown['tp'] == 0:
        penalty = breakdown['score'] - breakdown['fitness']
        print(f"\n⚠️  Recall below 10% and TP=0!")
        print(f"   Penalty applied: {penalty:.3f} points")
        print(f"   Operational impact: Rule is useless - detects no anomalies")
    else:
        print(f"\n✓ Recall meets 10% threshold or has TP > 0")


def demonstrate_degenerate_prevention():
    """Demonstrate degenerate collapse prevention."""
    print("\n" + "=" * 70)
    print("DEGENERATE COLLAPSE PREVENTION DEMONSTRATION")
    print("=" * 70)
    
    # Always-true rule
    always_true_tree = ("if_alert", True, "Always alerts")
    always_true_breakdown = fitness_breakdown(always_true_tree, seed=42, gen=0)
    
    # Always-false rule
    always_false_tree = ("if_alert", False, "Never alerts")
    always_false_breakdown = fitness_breakdown(always_false_tree, seed=42, gen=0)
    
    print(f"\nAlways-True Rule:")
    print(f"  Fitness: {always_true_breakdown['fitness']:.3f}")
    print(f"  Alert Rate: {always_true_breakdown['alert_rate']:.3f} ({always_true_breakdown['alert_rate']*100:.2f}%)")
    print(f"  ⚠️  Degenerate solution - always fires, heavy penalty")
    
    print(f"\nAlways-False Rule:")
    print(f"  Fitness: {always_false_breakdown['fitness']:.3f}")
    print(f"  TP: {always_false_breakdown['tp']}, FP: {always_false_breakdown['fp']}")
    print(f"  ⚠️  Degenerate solution - never fires, explicit penalty")
    
    # Good rule for comparison
    good_tree = ("if_alert", (">", ("max", "latency"), 75), "High latency")
    good_breakdown = fitness_breakdown(good_tree, seed=42, gen=0)
    
    print(f"\nGood Rule (for comparison):")
    print(f"  Rule: {good_tree}")
    print(f"  Fitness: {good_breakdown['fitness']:.3f}")
    print(f"  Precision: {good_breakdown['precision']:.3f} ({good_breakdown['precision']*100:.1f}%)")
    print(f"  FPR: {good_breakdown['fpr']:.3f} ({good_breakdown['fpr']*100:.1f}%)")
    print(f"  Alert Rate: {good_breakdown['alert_rate']:.3f} ({good_breakdown['alert_rate']*100:.2f}%)")
    print(f"  ✓ Non-degenerate - meets operational constraints")


def demonstrate_baseline_comparison():
    """Demonstrate baseline verification."""
    print("\n" + "=" * 70)
    print("BASELINE COMPARISON DEMONSTRATION")
    print("=" * 70)
    
    # A reasonable evolved rule
    champion_tree = ("if_alert", (">", ("max", "latency"), 75), "High latency detected")
    breakdown = fitness_breakdown(champion_tree, seed=42, gen=0)
    
    print("\nEvolved Champion:")
    print(f"  Rule: {champion_tree}")
    print(f"  Fitness: {breakdown['fitness']:.3f}")
    
    # Compare against baselines
    always_false = baseline_always_false(seed=42, gen=0)
    always_true = baseline_always_true(seed=42, gen=0)
    random_baseline = baseline_random(seed=42, gen=0, threshold=50.0)
    
    print(f"\nBaselines:")
    print(f"  Always-False: Fitness={always_false['fitness']:.3f}")
    print(f"  Always-True:  Fitness={always_true['fitness']:.3f}")
    print(f"  Random:       Fitness={random_baseline['fitness']:.3f}")
    
    print(f"\nComparison:")
    improvement_false = breakdown['fitness'] - always_false['fitness']
    improvement_true = breakdown['fitness'] - always_true['fitness']
    improvement_random = breakdown['fitness'] - random_baseline['fitness']
    
    print(f"  vs Always-False: {improvement_false:+.3f}")
    print(f"  vs Always-True:  {improvement_true:+.3f}")
    print(f"  vs Random:       {improvement_random:+.3f}")
    
    if breakdown['fitness'] > max(always_false['fitness'], always_true['fitness'], random_baseline['fitness']):
        print(f"\n✓ Champion beats all baselines - alignment working correctly!")
    else:
        print(f"\n⚠️  WARNING: Champion doesn't beat all baselines!")
        print(f"   This suggests alignment may not be working correctly.")


def main():
    """Run all alignment demonstrations."""
    print("\n" + "=" * 70)
    print("FITNESS ALIGNMENT DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows how fitness alignment ensures that 'high fitness'")
    print("means 'operationally useful', not just 'numerically high'.")
    print("\nSee docs/FITNESS_ALIGNMENT.md for comprehensive documentation.")
    
    demonstrate_precision_pressure()
    demonstrate_fpr_penalty()
    demonstrate_alert_rate_bands()
    demonstrate_recall_floor()
    demonstrate_degenerate_prevention()
    demonstrate_baseline_comparison()
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("1. Precision pressure ensures rules meet human-paged alert cost models (≥30%)")
    print("2. FPR penalties keep operational noise within tolerance (≤15%)")
    print("3. Alert-rate bands ensure deployment feasibility (0.2%-20%)")
    print("4. Recall floors guarantee minimum usefulness (≥10%)")
    print("5. Degenerate solutions (always-true/always-false) are eliminated")
    print("6. Baseline comparison validates alignment is working correctly")
    print("\nFor more information, see docs/FITNESS_ALIGNMENT.md")


if __name__ == "__main__":
    main()
