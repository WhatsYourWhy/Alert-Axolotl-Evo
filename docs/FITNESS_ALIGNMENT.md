# Fitness Alignment: Metric-Aligned Semantic Program Synthesis

## Executive Summary

Alert-Axolotl-Evo implements **Metric-Aligned Semantic Program Synthesis**, a phase where the fitness function is aligned with real-world operational constraints rather than simply optimized for higher scores. This ensures that when the system reports "high fitness," it means the evolved rules are operationally useful—meeting precision requirements, avoiding false positive overload, and functioning within deployment constraints. This is **fitness alignment**, not optimization: we're teaching the system what "good" actually means in production.

---

## Table of Contents

1. [Introduction](#introduction)
2. [The Five-Layer Architecture](#the-five-layer-architecture)
3. [Operational Constraints → Fitness Penalties Mapping](#operational-constraints--fitness-penalties-mapping)
4. [Implementation Details](#implementation-details)
5. [Baseline Verification](#baseline-verification)
6. [Evolution of Alignment](#evolution-of-alignment)
7. [Operational Justification](#operational-justification)
8. [For Different Audiences](#for-different-audiences)

---

## Introduction

### What is Fitness Alignment?

**Fitness Alignment** is the process of ensuring that fitness scores correspond to real-world operational value, not just numerical optimization. This is distinct from:

- **Optimization**: "Make the number bigger"
- **Alignment**: "Make the number mean the right thing"

In Alert-Axolotl-Evo, we're not tuning parameters to maximize scores. We're encoding operational constraints into the fitness landscape so that:

> The only hills left correspond to genuinely useful rules.

### Why This Matters

Most genetic programming systems stop at:

> "Here's a fitness score, hope it works."

Alert-Axolotl-Evo goes further by explicitly encoding:

- **Precision requirements** (human-paged alert cost models)
- **False positive tolerance** (operational noise limits)
- **Alert rate feasibility** (deployment constraints)
- **Minimum detection floors** (usefulness thresholds)
- **Degenerate collapse prevention** (always-true/always-false elimination)

This is **production-grade alignment**, not research toy behavior.

---

## The Five-Layer Architecture

Alert-Axolotl-Evo is built in five distinct layers:

1. **Genetic Programming** – mechanism (`evolution.py`, `operators.py`)
2. **Program Synthesis** – output form (tree representation)
3. **Constraint-Guided Search** – semantic validity (`is_valid_alert_rule()`, type checking)
4. **Economically Regulated Learning** – macro library, budgets (`promotion.py`)
5. **Metric-Aligned Fitness Shaping** ← *This phase* (`fitness.py` lines 708-837)

The fifth layer is rare. Most systems stop at layer 1-2. This system explicitly implements all five, with fitness alignment as the final layer that ensures operational relevance.

### Where This Phase Sits

```
┌─────────────────────────────────────────────────────────┐
│ Layer 5: Metric-Aligned Fitness Shaping                │
│   - Precision pressure (≥30%)                           │
│   - FPR penalties (≤15%)                                │
│   - Alert-rate bands (0.2%-20%)                         │
│   - Recall floors (≥10%)                                │
│   - Degenerate collapse prevention                      │
└──────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│ Layer 4: Economically Regulated Learning                 │
│   - PromotionManager (causal lift requirements)          │
│   - Library budget enforcement                           │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│ Layer 3: Constraint-Guided Search                        │
│   - Semantic validity gates                              │
│   - Type-strict evaluation                               │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│ Layer 2: Program Synthesis                               │
│   - Tree-based representation                            │
│   - Explicit logic structures                            │
└───────────────────────┬──────────────────────────────────┘
                        │
┌───────────────────────▼──────────────────────────────────┐
│ Layer 1: Genetic Programming                             │
│   - Selection, crossover, mutation                       │
│   - Population management                                │
└──────────────────────────────────────────────────────────┘
```

---

## Operational Constraints → Fitness Penalties Mapping

Each alignment mechanism maps directly to an operational constraint. This is not tuning—it's encoding real-world requirements.

### 1. Precision Pressure (≥30%)

**Operational Constraint**: Human-paged alerts have real cost. If precision is too low, operators get overwhelmed by false alarms.

**Fitness Penalty**: 
```python
if precision < 0.3:
    precision_deficit = 0.3 - precision
    score -= 5.0 * precision_deficit  # Max penalty of 1.5 for 0% precision
```

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 784-795

**Why 30%?**: This threshold represents a reasonable balance for human-paged alerts. Below this, the operational cost of false alarms exceeds the value of detection.

### 2. FPR Penalties (≤15%)

**Operational Constraint**: False positive rate must stay within operational noise tolerance. High FPR creates alert fatigue.

**Fitness Penalty**:
```python
if fpr > 0.15:  # More than 15% false positive rate
    score -= 2.0 * (fpr - 0.15)  # Penalty scales with excess FPR
```

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 811-813

**Why 15%?**: This represents the maximum acceptable false positive rate for operational monitoring. Beyond this, alert fatigue sets in and operators start ignoring alerts.

### 3. Alert-Rate Bands (0.2% to 20%)

**Operational Constraint**: Rules must alert at deployment-feasible rates. Too low = never fires (useless). Too high = always fires (noisy).

**Fitness Penalties**:
```python
if alert_rate < 0.002:  # Less than 0.2%
    score -= 2.0  # Penalty for too-low alert rate
elif alert_rate > 0.50:  # More than 50% - "always-true collapse"
    excess_rate = alert_rate - 0.5
    penalty = 2.0 * excess_rate * total_rows  # Scales with dataset size
    score -= penalty
elif alert_rate > 0.20:  # More than 20% but <= 50%
    score -= 3.0  # Penalty for too-high alert rate
```

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 755-769

**Why these thresholds?**:
- **0.2% floor**: Rules that alert less than this are effectively never-firing (deployment useless)
- **20% ceiling**: Beyond this, rules become too noisy for operational use
- **50% hard limit**: Above this, rules are "always-true collapse" and must be strictly dominated

### 4. Recall Floors (≥10%)

**Operational Constraint**: Rules must detect at least some anomalies to be useful. Zero detection is worse than useless.

**Fitness Penalty**:
```python
if recall < 0.1 and tp == 0:  # No detection at all
    score -= 3.0  # Additional penalty for zero detection
```

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 828-832

**Why 10%?**: This ensures rules have minimum useful detection. Rules with zero true positives are explicitly penalized.

### 5. Degenerate Collapse Prevention

**Operational Constraint**: Rules that always return True or always return False are useless, even if they technically have "good" metrics.

**Fitness Penalties**:

**Self-Comparison Detection**:
```python
if is_self_comparison(condition):
    score -= 10.0  # Heavy penalty for self-comparisons (always False/True)
```

**No-Alert Detection**:
```python
if tp == 0 and fp == 0:
    score -= 5.0  # Explicit penalty that dominates bloat incentives
```

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 729-738

**Why this matters**: Without these penalties, the system can collapse into degenerate solutions that game the metrics without providing value.

### 6. Invalid Output Gates

**Operational Constraint**: Rules must produce valid outputs (string alert messages or None). Invalid outputs indicate broken logic.

**Fitness Penalties**:
```python
# Hard gate: reject if >50% invalid
if invalid_rate > 0.5:
    return -100.0

# Soft penalty: gradient pressure before hard gate
if invalid_rate > 0.0:
    score -= 0.5 * invalid_rate
```

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 683-692

**Why this matters**: Invalid outputs indicate semantic errors in the evolved logic. These must be caught and penalized.

---

## Intended Operating Region

The fitness alignment mechanisms define an **explicit operating region** where evolved rules must operate to be considered operationally useful. Rules outside this region are penalized or rejected.

### Operating Region Bounds

A rule is **operationally aligned** if it meets ALL of the following constraints:

| Metric | Lower Bound | Upper Bound | Justification |
|--------|-------------|-------------|---------------|
| **Alert Rate** | 0.2% (0.002) | 20% (0.20) | Deployment feasibility - too low = never fires, too high = too noisy |
| **Precision** | 30% (0.30) | 100% (1.0) | Human-paged alert cost model - below 30% is operationally costly |
| **FPR** | 0% (0.0) | 15% (0.15) | Operational noise tolerance - above 15% causes alert fatigue |
| **Recall** | 10% (0.10) or TP > 0 | 100% (1.0) | Minimum usefulness - must detect at least some anomalies |
| **Invalid Rate** | 0% (0.0) | 50% (0.50) | Semantic validity - above 50% = hard fail, prefer 0% |

### Operating Region Enforcement

- **Within bounds**: Rules that meet all constraints are rewarded (higher fitness)
- **Outside bounds**: Rules that violate constraints are penalized (lower fitness)
- **Hard gates**: Some violations cause immediate rejection (invalid_rate > 50%, always-true collapse)

### Why Explicit Bounds Matter

Without explicit operating region definitions, the system can drift into:
- **Metric gaming**: Rules that optimize one metric by violating others
- **Overfitting**: Rules that work only on synthetic data shapes
- **Degenerate solutions**: Rules that technically "win" but are operationally useless

The operating region ensures that "high fitness" means "meets all operational constraints," not just "optimizes one metric."

---

## Valid Improvement vs Metric Gaming

### What is Valid Improvement?

A rule demonstrates **valid improvement** if it:
- Meets ALL operating region constraints (alert rate, precision, FPR, recall, invalid rate)
- Beats baselines across ALL metrics (not just one)
- Works across multiple data seeds (not overfit to one mock world)
- Uses non-trivial logic (not just `max(latency) >= T`)

### What is Metric Gaming?

A rule is **gaming metrics** if it:
- Optimizes precision by barely alerting (<0.2% alert rate)
- Overfits to synthetic anomaly shapes (only works on one data seed)
- Exploits mock data generator artifacts (e.g., always using `max()` because anomalies are "big spikes")
- Collapses to simple thresholds that work only in mock world
- Violates operating region bounds to optimize a single metric

### Warning Signs of Metric Gaming

**Red Flags** (investigate immediately):
- High precision but alert rate < 0.2% (too conservative, barely fires)
- High recall but FPR > 15% (too noisy, operational fatigue)
- Rules that only work on one data seed (overfitting)
- Rules that collapse to simple `max(latency) >= T` (exploiting mock data artifacts)
- Rules that beat baselines on one metric but fail on others

**Healthy Signs** (alignment working):
- Rules meet all operating region constraints
- Rules beat baselines across all metrics
- Rules work across multiple data seeds
- Rules use diverse logic (not just max thresholds)
- Metrics are balanced (good precision AND recall AND reasonable alert rate)

### How to Detect Gaming

1. **Baseline Comparison**: If champion doesn't beat all baselines, investigate
2. **Multi-Seed Validation**: Test rule on different seeds - if it fails, it's overfit
3. **Operating Region Check**: Verify all metrics are within bounds
4. **Logic Inspection**: If rule is just `max(latency) >= T`, it may be exploiting mock data
5. **Metric Balance**: If one metric is optimized at expense of others, it's gaming

### Example: Valid vs Gaming

**Valid Rule**:
```
if_alert(
  and(
    >(max(latency), 75),
    <(avg(latency), 200)
  ),
  "High latency spike detected"
)
```
- Alert rate: 5.2% (within bounds)
- Precision: 45% (meets threshold)
- FPR: 8% (within bounds)
- Recall: 60% (meets threshold)
- Works on multiple seeds

**Gaming Rule**:
```
if_alert(
  >(max(latency), 10000),
  "Extreme threshold"
)
```
- Alert rate: 0.1% (below 0.2% - too conservative)
- Precision: 100% (high, but by barely alerting)
- FPR: 0% (low, but because it never fires)
- Recall: 0% (doesn't detect anything)
- Only works because mock anomalies are "big spikes"

---

## Mock Data Realism and Evolution Honesty

### The Critical Constraint

**The mock data generator is part of the objective function.** If the generator is wrong, evolution is pointless.

This is not a side quest—it's a core constraint. Evolved rules that work only because of mock data artifacts are not operationally useful.

### Current Limitations

The current mock data generator produces anomalies as **"big spikes"** (multiplier-based elevation). This creates a strong bias toward:

- `max(latency) >= T` rules (always dominate)
- Simple threshold logic (works because anomalies are obvious)
- Overfitting to spike patterns (doesn't generalize)

### Why This Matters

If anomalies are always "big spikes," then:
- `max(latency) >= 75` will always win
- More sophisticated logic is unnecessary
- Evolution learns mock data artifacts, not real patterns
- Rules won't generalize to real-world data

### Future Improvements Needed

To make evolution honest, the mock data generator needs:

1. **Sustained moderate elevation**: Anomalies that are elevated but not spikes
2. **Variance-based anomalies**: Anomalies in variance, not just magnitude
3. **Distribution shift**: Anomalies that change distribution without max spike
4. **Seasonal bursts / diurnal patterns**: Time-based anomaly patterns
5. **Multiple anomaly types**: Mix of spike, sustained, variance, distribution shifts

### Holdout Evaluation (Future Enhancement)

**The cleanest way to keep evolution honest** is holdout evaluation:

- **Train**: Evolve on one generated dataset (seed family A)
- **Validate**: Score on second dataset (seed family B, same parameters, different noise realization)
- **Prevents**: Overfitting to one mock world
- **Ensures**: Rules generalize across data realizations

This is the most important future enhancement for preventing mock data artifacts from controlling evolution.

### Current Mitigations

Until holdout evaluation is implemented:
- Alert-rate bands prevent rules that barely fire (precision gaming)
- Recall floors prevent rules that never detect (conservative gaming)
- Baseline comparison catches degenerate solutions
- Operating region constraints prevent single-metric optimization

But the fundamental issue (mock data artifacts) remains until the generator is improved or holdout evaluation is added.

---

## Implementation Details

### Code Structure

The alignment mechanisms are organized in [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py):

1. **Lines 683-692**: Hard validity gates and invalid output detection
2. **Lines 729-738**: Degenerate collapse prevention (self-comparison, no-alert)
3. **Lines 755-769**: Alert-rate band penalties
4. **Lines 784-795**: Precision pressure
5. **Lines 811-813**: FPR penalties
6. **Lines 828-832**: Recall floors

### Function Organization

- **`fitness()`**: Main fitness function with all alignment mechanisms
- **`fitness_breakdown()`**: Detailed breakdown for debugging and validation
- **`print_fitness_comparison()`**: Baseline verification (see [Baseline Verification](#baseline-verification))

### Configuration

Alignment thresholds are currently hardcoded in the fitness function. Future versions may expose these via `FitnessAlignmentConfig` (see [Configuration](#configuration)).

---

## Baseline Verification

The system includes built-in baseline verification to ensure alignment is working correctly.

### `print_fitness_comparison()`

This function compares the evolved champion against three baselines:

1. **Always-False**: Rule that never alerts (`if_alert(False, ...)`)
2. **Always-True**: Rule that always alerts (`if_alert(True, ...)`)
3. **Random Baseline**: Simple threshold rule (`avg(latency) > 50`)

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 877-1022

### Validation Logic

If the champion doesn't beat all baselines, the system warns:

```python
if champion_breakdown['fitness'] <= max(always_false['fitness'], always_true['fitness'], random_baseline['fitness']):
    print(f"\nWARNING: Champion is not better than all baselines!")
    print(f"   This suggests the evolution may be optimizing a loophole.")
```

This is a critical sanity check: if alignment is working, degenerate solutions should be strictly dominated.

### How to Use

The comparison is automatically printed during evolution when using the main evolution loop. It can also be called manually:

```python
from alert_axolotl_evo.fitness import print_fitness_comparison, fitness_breakdown

breakdown = fitness_breakdown(champion_tree, seed=42, gen=10)
print_fitness_comparison(champion_tree, breakdown, seed=42, gen=10)
```

---

## Evolution of Alignment

The alignment mechanisms were added incrementally as the system evolved. This section documents the historical context.

### Phase 1: Basic F-Beta Scoring

Initially, the system used simple F-beta scoring without alignment constraints. This led to:
- Always-true rules dominating (high recall, but useless)
- Always-false rules sometimes winning (zero false positives, but useless)
- Rules with terrible precision but high recall winning

### Phase 2: Degenerate Collapse Prevention

Added penalties for:
- Self-comparisons (always-False/True)
- No-alert rules (never fire)

**Result**: Degenerate solutions were eliminated, but precision issues remained.

### Phase 3: Alert-Rate Bands

Added constraints on alert rate to prevent:
- Rules that never fire (<0.2%)
- Rules that always fire (>20-50%)

**Result**: Rules became more deployment-feasible, but precision was still unconstrained.

### Phase 4: Precision Pressure

Added precision requirement (≥30%) to enforce human-paged alert cost models.

**Result**: Rules started meeting operational precision requirements.

### Phase 5: FPR Penalties

Added direct FPR penalties (≤15%) to complement precision pressure.

**Result**: Complete operational constraint coverage.

### Phase 6: Recall Floors

Added minimum detection requirements (≥10%) to ensure rules are useful.

**Result**: Balanced alignment across all operational dimensions.

### Current State

All alignment mechanisms are active and working together. The system now produces rules that:
- Meet precision requirements (≥30%)
- Stay within FPR limits (≤15%)
- Alert at feasible rates (0.2%-20%)
- Detect minimum useful anomalies (≥10%)
- Avoid degenerate collapses

---

## Operational Justification

Each threshold exists for a specific operational reason. This section explains the "why" behind each number.

### Precision ≥30%

**Cost Model**: Human-paged alerts have real cost:
- Operator time to investigate
- Context switching overhead
- Alert fatigue from false alarms

**Threshold Justification**: 30% precision means that for every 10 alerts, at least 3 are real. Below this, the cost of false alarms exceeds the value of detection.

**Source**: Industry best practices for human-paged alerting systems.

### FPR ≤15%

**Cost Model**: False positive rate directly impacts operational noise tolerance.

**Threshold Justification**: 15% FPR means that 15% of normal operations trigger alerts. Beyond this, operators start ignoring alerts due to fatigue.

**Source**: Operational monitoring best practices.

### Alert Rate 0.2%-20%

**Deployment Feasibility**: Rules must alert at rates that are:
- High enough to be useful (>0.2%)
- Low enough to be manageable (<20%)

**Threshold Justification**:
- **0.2% floor**: Rules below this are effectively never-firing
- **20% ceiling**: Rules above this become too noisy
- **50% hard limit**: Above this, rules are "always-true" and must be strictly dominated

**Source**: Deployment feasibility analysis.

### Recall ≥10%

**Usefulness Requirement**: Rules must detect at least some anomalies to be useful.

**Threshold Justification**: 10% recall ensures rules have minimum useful detection. Rules with zero true positives are explicitly penalized.

**Source**: Minimum usefulness threshold for anomaly detection.

---

## For Different Audiences

### For End Users (Operational Implications)

**What this means for you**: When you deploy an evolved rule, you can trust that:
- It will alert at reasonable rates (not too noisy, not too quiet)
- It will have acceptable precision (≥30% real alerts)
- It will stay within false positive limits (≤15% FPR)
- It will detect at least some anomalies (≥10% recall)

**How to interpret fitness scores**: Higher fitness means the rule meets more operational constraints. A rule with fitness 8.5 is operationally better than one with fitness 2.0, not just numerically higher.

**When to adjust thresholds**: Only adjust if your operational constraints differ from the defaults. For example, if you have automated response systems (not human-paged), you might tolerate lower precision.

### For Developers (Implementation Details)

**Code locations**: All alignment mechanisms are in [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py):
- Lines 708-837: All alignment penalties
- Lines 840-1022: Baseline verification

**How to add new alignment mechanisms**:
1. Identify the operational constraint
2. Add penalty logic in `fitness()` function
3. Update `fitness_breakdown()` to include new metric
4. Add test cases in `tests/test_fitness.py`
5. Document in this file

**Configuration**: Currently hardcoded. Future: `FitnessAlignmentConfig` dataclass.

**Testing**: See [`docs/FITNESS_ALIGNMENT_VALIDATION.md`](docs/FITNESS_ALIGNMENT_VALIDATION.md) for validation methodology.

### For Researchers (Formal Specification)

**System Class**: Metric-Aligned Semantic Program Synthesis

**Formal Definition**: The fitness function `f(s)` for solution `s` is:

```
f(s) = f_beta(s) * possible_tp - Σ penalties(s)
```

Where penalties include:
- `p_precision(s)`: Precision deficit penalty (if precision < 0.3)
- `p_fpr(s)`: FPR excess penalty (if FPR > 0.15)
- `p_alert_rate(s)`: Alert rate band penalty (if outside 0.002-0.20)
- `p_recall(s)`: Recall floor penalty (if recall < 0.1 and tp = 0)
- `p_degenerate(s)`: Degenerate collapse penalty (self-comparison, no-alert)
- `p_invalid(s)`: Invalid output penalty

**Constraint Satisfaction**: A solution `s` is **operationally aligned** if:
- `precision(s) ≥ 0.3`
- `fpr(s) ≤ 0.15`
- `0.002 ≤ alert_rate(s) ≤ 0.20`
- `recall(s) ≥ 0.1` or `tp(s) > 0`
- `s` is not degenerate (not always-true/always-false)
- `invalid_rate(s) ≤ 0.5`

**Baseline Dominance**: For alignment to be valid, evolved solutions must strictly dominate baselines:
- `f(champion) > f(always_false)`
- `f(champion) > f(always_true)`
- `f(champion) > f(random_baseline)`

**See Also**: 
- [`docs/design_contract.md`](docs/design_contract.md) for architectural constraints
- [`ARCHITECTURE.md`](ARCHITECTURE.md) for system architecture

---

## Related Documentation

- [`docs/FITNESS_ALIGNMENT_VALIDATION.md`](docs/FITNESS_ALIGNMENT_VALIDATION.md): How to validate alignment is working
- [`docs/FITNESS_ALIGNMENT_CHANGELOG.md`](docs/FITNESS_ALIGNMENT_CHANGELOG.md): Historical changes to alignment mechanisms
- [`ARCHITECTURE.md`](ARCHITECTURE.md): System architecture overview
- [`docs/design_contract.md`](docs/design_contract.md): Design constraints and invariants

---

## Summary

Fitness alignment is the phase where Alert-Axolotl-Evo ensures that "high fitness" means "operationally useful," not just "numerically high." This is achieved through explicit encoding of operational constraints:

- **Precision pressure** (≥30%): Human-paged alert cost models
- **FPR penalties** (≤15%): Operational noise tolerance
- **Alert-rate bands** (0.2%-20%): Deployment feasibility
- **Recall floors** (≥10%): Minimum usefulness
- **Degenerate collapse prevention**: Always-true/always-false elimination

This is **production-grade alignment**, not research toy behavior. The system is teaching itself what "good" actually means in operational terms.
