"""
Fitness evaluation: tree evaluation, scoring, baselines.

This package is organized by concern:

- evaluator: tree evaluation (`evaluate`) and synthetic data generation
- alignment: operationally-aligned fitness scoring (`fitness`, `fitness_breakdown`)
- baselines: degenerate-rule baselines and comparison reporting

The public API below is re-exported for backward compatibility; prefer the
submodules for new code.

Alignment mechanisms are documented in docs/fitness-alignment.md.
"""

from alert_axolotl_evo.fitness.alignment import fitness, fitness_breakdown
from alert_axolotl_evo.fitness.baselines import (
    BaselineComparisonFailed,
    baseline_always_false,
    baseline_always_true,
    baseline_random,
    print_fitness_comparison,
)
from alert_axolotl_evo.fitness.evaluator import (
    coerce_number,
    evaluate,
    generate_mock_data,
)

__all__ = [
    "BaselineComparisonFailed",
    "baseline_always_false",
    "baseline_always_true",
    "baseline_random",
    "coerce_number",
    "evaluate",
    "fitness",
    "fitness_breakdown",
    "generate_mock_data",
    "print_fitness_comparison",
]
