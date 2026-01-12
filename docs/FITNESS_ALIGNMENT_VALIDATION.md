# Fitness Alignment Validation

This document describes how to validate that fitness alignment is working correctly, how to detect alignment drift, and how to test alignment mechanisms.

## Overview

Fitness alignment validation ensures that:
1. Alignment mechanisms are active and working
2. Evolved solutions strictly dominate degenerate baselines
3. Alignment thresholds are appropriate for your use case
4. No alignment drift has occurred (metric soup, over-penalization)

## Baseline Verification

### What is Baseline Verification?

Baseline verification compares evolved champions against three degenerate baselines:
1. **Always-False**: Rule that never alerts (`if_alert(False, ...)`)
2. **Always-True**: Rule that always alerts (`if_alert(True, ...)`)
3. **Random Baseline**: Simple threshold rule (`avg(latency) > 50`)

If alignment is working correctly, evolved champions should **strictly dominate** all baselines.

### How to Run Baseline Verification

The system includes built-in baseline verification via `print_fitness_comparison()`:

```python
from alert_axolotl_evo.fitness import print_fitness_comparison, fitness_breakdown

# After evolution, get champion breakdown
breakdown = fitness_breakdown(champion_tree, seed=42, gen=10)

# Compare against baselines
print_fitness_comparison(champion_tree, breakdown, seed=42, gen=10)
```

### Expected Output

```
======================================================================
  FITNESS BREAKDOWN COMPARISON
======================================================================

CHAMPION:
  Tree: ('if_alert', ('>', ('max', 'latency'), 75), 'High latency!')
  Fitness: 8.523
  TP: 45, FP: 12, FN: 5
  Recall: 0.900 (90.0%)
  Precision: 0.789 (78.9%)
  FPR: 0.127 (12.7%)
  F-beta: 0.852
  Alert Rate: 0.057 (5.7%), Invalid Rate: 0.000 (0.0%)
  Node Count: 5

BASELINES:
  Always-False: Fitness=-5.000, TP=0, FP=0, FN=50
  Always-True:  Fitness=-950.000, TP=50, FP=950, FN=0
  Random (avg>50): Fitness=2.341, TP=30, FP=45, FN=20

CHAMPION vs BASELINES:
  vs Always-False: +13.523
  vs Always-True:  +958.523
  vs Random:       +6.182
```

### Warning Signs

If you see this warning:

```
WARNING: Champion is not better than all baselines!
   This suggests the evolution may be optimizing a loophole.
```

This indicates:
- Alignment mechanisms may not be working correctly
- A loophole in the fitness function exists
- Thresholds may need adjustment

**Action**: Investigate why the champion doesn't dominate baselines. Check:
1. Are alignment penalties being applied?
2. Are thresholds appropriate for your data?
3. Is there a bug in the fitness function?

## Testing Alignment Mechanisms

### Manual Testing

You can manually test each alignment mechanism:

```python
from alert_axolotl_evo.fitness import fitness_breakdown

# Test precision pressure
# Create a rule with low precision (many false positives)
low_precision_tree = ("if_alert", (">", ("avg", "latency"), 10), "Low threshold")
breakdown = fitness_breakdown(low_precision_tree, seed=42, gen=0)
print(f"Precision: {breakdown['precision']:.3f}")
print(f"Fitness: {breakdown['fitness']:.3f}")
# Should see penalty applied if precision < 0.3

# Test FPR penalty
# Create a rule with high false positive rate
high_fpr_tree = ("if_alert", (">", ("avg", "latency"), 5), "Very low threshold")
breakdown = fitness_breakdown(high_fpr_tree, seed=42, gen=0)
print(f"FPR: {breakdown['fpr']:.3f}")
print(f"Fitness: {breakdown['fitness']:.3f}")
# Should see penalty applied if FPR > 0.15

# Test alert-rate bands
# Create an always-true rule
always_true_tree = ("if_alert", True, "Always alerts")
breakdown = fitness_breakdown(always_true_tree, seed=42, gen=0)
print(f"Alert Rate: {breakdown['alert_rate']:.3f}")
print(f"Fitness: {breakdown['fitness']:.3f}")
# Should see heavy penalty (scales with dataset size)

# Test recall floor
# Create a rule that never detects anomalies
never_detects_tree = ("if_alert", (">", ("avg", "latency"), 1000), "Too high")
breakdown = fitness_breakdown(never_detects_tree, seed=42, gen=0)
print(f"Recall: {breakdown['recall']:.3f}, TP: {breakdown['tp']}")
print(f"Fitness: {breakdown['fitness']:.3f}")
# Should see penalty if recall < 0.1 and tp == 0
```

### Automated Testing

See `tests/test_fitness.py` for automated test cases covering:
- Precision pressure enforcement
- FPR penalty application
- Alert-rate band penalties
- Recall floor enforcement
- Degenerate collapse prevention
- Baseline comparison validation

Run tests:

```bash
pytest tests/test_fitness.py -v
```

## Detecting Alignment Drift

### What is Alignment Drift?

Alignment drift occurs when:
1. **Metric Soup**: Too many competing metrics without clear operational justification
2. **Over-Penalization**: Penalties become so strong that no solutions can succeed
3. **Fragile Reward Shaping**: Small changes to thresholds cause large fitness swings
4. **Loophole Exploitation**: System finds ways to game metrics without providing value

### Signs of Alignment Drift

**Warning Signs**:
- Fitness scores consistently negative
- No solutions beat baselines
- Evolution converges to degenerate solutions
- Small threshold changes cause dramatic fitness changes
- Metrics conflict (high precision but terrible recall, etc.)

**Healthy Signs**:
- Champions consistently beat baselines
- Fitness scores are positive and meaningful
- Solutions meet operational constraints
- Metrics are balanced (good precision AND recall)
- Threshold changes have predictable effects

### How to Check for Drift

1. **Baseline Comparison**: Run baseline verification regularly. If champions stop beating baselines, drift may have occurred.

2. **Metric Analysis**: Check if metrics are balanced:
   ```python
   breakdown = fitness_breakdown(champion_tree, seed=42, gen=10)
   
   # Check if metrics are balanced
   assert breakdown['precision'] >= 0.3, "Precision too low"
   assert breakdown['fpr'] <= 0.15, "FPR too high"
   assert 0.002 <= breakdown['alert_rate'] <= 0.20, "Alert rate out of band"
   assert breakdown['recall'] >= 0.1 or breakdown['tp'] > 0, "No detection"
   ```

3. **Threshold Sensitivity**: Test if small threshold changes cause large fitness swings:
   ```python
   # Test threshold sensitivity
   base_fitness = fitness(tree, seed=42, gen=10)
   
   # Slightly adjust alignment config
   config.fitness_alignment.min_precision = 0.31  # +0.01
   adjusted_fitness = fitness(tree, seed=42, gen=10, fitness_config=config.fitness)
   
   # Fitness change should be reasonable, not dramatic
   fitness_delta = abs(adjusted_fitness - base_fitness)
   assert fitness_delta < 5.0, "Thresholds too sensitive"
   ```

4. **Evolutionary Behavior**: Monitor evolution:
   - Do solutions improve over generations?
   - Do they converge to useful rules?
   - Or do they collapse to degenerate solutions?

## Operating Region Validation

### What is the Operating Region?

The operating region defines explicit bounds where evolved rules must operate to be considered operationally useful. See [`docs/FITNESS_ALIGNMENT.md`](FITNESS_ALIGNMENT.md) for the complete operating region definition.

### Operating Region Bounds

| Metric | Lower Bound | Upper Bound |
|--------|-------------|-------------|
| Alert Rate | 0.2% (0.002) | 20% (0.20) |
| Precision | 30% (0.30) | 100% (1.0) |
| FPR | 0% (0.0) | 15% (0.15) |
| Recall | 10% (0.10) or TP > 0 | 100% (1.0) |
| Invalid Rate | 0% (0.0) | 50% (0.50) |

### How to Validate Operating Region

```python
from alert_axolotl_evo.fitness import fitness_breakdown

breakdown = fitness_breakdown(champion_tree, seed=42, gen=10)

# Validate all operating region bounds
assert breakdown['alert_rate'] >= 0.002, f"Alert rate {breakdown['alert_rate']:.4f} below 0.2%"
assert breakdown['alert_rate'] <= 0.20, f"Alert rate {breakdown['alert_rate']:.4f} above 20%"
assert breakdown['precision'] >= 0.3, f"Precision {breakdown['precision']:.3f} below 30%"
assert breakdown['fpr'] <= 0.15, f"FPR {breakdown['fpr']:.3f} above 15%"
assert breakdown['recall'] >= 0.1 or breakdown['tp'] > 0, "Recall below 10% and TP=0"
assert breakdown['invalid_rate'] <= 0.5, f"Invalid rate {breakdown['invalid_rate']:.3f} above 50%"

print("✓ All operating region constraints met")
```

### Operating Region Violations

If a rule violates operating region bounds:
- **Investigate**: Why did it violate? Is it a bug or legitimate edge case?
- **Check penalties**: Are alignment penalties being applied?
- **Review thresholds**: Are thresholds appropriate for your use case?
- **Consider context**: Some violations may be acceptable in specific contexts (document why)

## Metric Gaming Detection

### What is Metric Gaming?

Metric gaming occurs when rules optimize one metric by violating others or exploiting mock data artifacts. See [`docs/FITNESS_ALIGNMENT.md`](FITNESS_ALIGNMENT.md) for complete definition.

### How to Detect Gaming

```python
from alert_axolotl_evo.fitness import fitness_breakdown

breakdown = fitness_breakdown(champion_tree, seed=42, gen=10)

# Check for gaming patterns
warnings = []

# Gaming: High precision but barely alerting
if breakdown['precision'] >= 0.5 and breakdown['alert_rate'] < 0.002:
    warnings.append("GAMING: High precision but alert rate < 0.2% (too conservative)")

# Gaming: High recall but too noisy
if breakdown['recall'] >= 0.8 and breakdown['fpr'] > 0.15:
    warnings.append("GAMING: High recall but FPR > 15% (too noisy)")

# Gaming: Simple max threshold (exploiting mock data)
import ast
tree_str = str(champion_tree)
if 'max' in tree_str and 'latency' in tree_str and tree_str.count('>') == 1:
    warnings.append("WARNING: Simple max threshold - may be exploiting mock data artifacts")

# Gaming: Overfitting (test on multiple seeds)
fitness_seed_42 = fitness(champion_tree, seed=42, gen=10)
fitness_seed_43 = fitness(champion_tree, seed=43, gen=10)
fitness_delta = abs(fitness_seed_42 - fitness_seed_43)
if fitness_delta > 5.0:  # Large variance across seeds
    warnings.append("WARNING: Large fitness variance across seeds (possible overfitting)")

if warnings:
    print("⚠️  Metric Gaming Detected:")
    for warning in warnings:
        print(f"   - {warning}")
else:
    print("✓ No metric gaming detected")
```

### Gaming Patterns to Watch For

1. **Precision Gaming**: Rules that optimize precision by barely alerting
   - Alert rate < 0.2% but precision > 50%
   - Solution: Alert-rate band penalty should catch this

2. **Mock Data Artifacts**: Rules that exploit mock data generator
   - Always using `max(latency) >= T` (works because anomalies are "big spikes")
   - Solution: Improve mock data generator or add holdout evaluation

3. **Overfitting**: Rules that work only on one data seed
   - Large fitness variance across seeds
   - Solution: Test on multiple seeds, add holdout evaluation

4. **Single-Metric Optimization**: Rules that optimize one metric at expense of others
   - High precision but terrible recall
   - High recall but terrible precision
   - Solution: Operating region constraints should prevent this

### Mock Data Artifact Detection

```python
# Test if rule is exploiting mock data artifacts
breakdown = fitness_breakdown(champion_tree, seed=42, gen=0)

# Check if rule is just a simple max threshold
tree_str = str(champion_tree)
is_simple_max = (
    'max' in tree_str and 
    'latency' in tree_str and 
    tree_str.count('>') == 1 and
    tree_str.count('if_alert') == 1
)

if is_simple_max:
    print("⚠️  WARNING: Rule is simple max threshold")
    print("   This may be exploiting mock data artifacts (anomalies are 'big spikes')")
    print("   Consider: Improving mock data generator or adding holdout evaluation")
```

## Validation Checklist

Use this checklist to validate alignment:

### Baseline Validation
- [ ] Champions beat all baselines (always-false, always-true, random)
- [ ] Baseline comparison runs and validates correctly
- [ ] No warnings about champions not beating baselines

### Operating Region Validation
- [ ] Alert rate in [0.2%, 20%] for evolved champions
- [ ] Precision ≥ 30% for evolved champions
- [ ] FPR ≤ 15% for evolved champions
- [ ] Recall ≥ 10% or TP > 0 for evolved champions
- [ ] Invalid rate ≤ 50% (prefer 0%) for evolved champions

### Metric Gaming Detection
- [ ] No precision gaming (high precision but alert rate < 0.2%)
- [ ] No recall gaming (high recall but FPR > 15%)
- [ ] No mock data artifact exploitation (simple max thresholds)
- [ ] No overfitting (rules work across multiple seeds)
- [ ] Metrics are balanced (not just one metric optimized)

### Degenerate Solution Prevention
- [ ] No degenerate solutions (always-true/always-false) win
- [ ] Self-comparison detection working
- [ ] No-alert penalty applied correctly

### General Health
- [ ] Fitness scores are positive and meaningful
- [ ] Threshold changes have predictable effects
- [ ] Automated tests pass
- [ ] Evolution converges to useful rules (not degenerate)

## Troubleshooting

### Problem: Champions don't beat baselines

**Possible Causes**:
- Alignment mechanisms not active
- Thresholds too strict
- Data mismatch (training vs validation)
- Bug in fitness function

**Solutions**:
1. Check if alignment penalties are being applied (inspect `fitness_breakdown()`)
2. Verify thresholds are appropriate for your data
3. Test with simpler rules first
4. Review fitness function code for bugs

### Problem: All fitness scores are negative

**Possible Causes**:
- Over-penalization (thresholds too strict)
- Data issues (no anomalies, wrong format)
- Alignment mechanisms too aggressive

**Solutions**:
1. Check if baselines also have negative fitness (expected)
2. Verify data has anomalies
3. Consider relaxing thresholds slightly
4. Check if invalid output rate is high (indicates tree evaluation issues)

### Problem: Evolution converges to degenerate solutions

**Possible Causes**:
- Degenerate collapse prevention not working
- Alignment mechanisms not strong enough
- Search space too constrained

**Solutions**:
1. Verify self-comparison detection is working
2. Check no-alert penalty is being applied
3. Increase penalty magnitudes if needed
4. Review evolution operators (crossover, mutation)

### Problem: Metrics conflict (high precision, terrible recall)

**Possible Causes**:
- Precision pressure too strong
- Recall floor too weak
- F-beta weighting inappropriate
- Metric gaming (optimizing one metric at expense of others)

**Solutions**:
1. Check operating region validation - rules must meet ALL bounds
2. Adjust F-beta parameter (beta in FitnessConfig)
3. Balance precision and recall penalties
4. Consider multi-objective optimization
5. Review operational requirements (which matters more?)
6. Check for metric gaming patterns (see Metric Gaming Detection section)

### Problem: Rules exploit mock data artifacts

**Possible Causes**:
- Mock data generator too simple (only "big spikes")
- Rules collapse to simple `max(latency) >= T` thresholds
- Overfitting to mock data shapes

**Solutions**:
1. Improve mock data generator (add sustained elevation, variance anomalies, etc.)
2. Add holdout evaluation (train on one seed, validate on another)
3. Test rules on multiple seeds to detect overfitting
4. Consider penalizing simple max thresholds if they dominate
5. Acknowledge limitation: Current mock data favors max() rules

### Problem: Operating region violations

**Possible Causes**:
- Alignment mechanisms not working
- Thresholds inappropriate for use case
- Data characteristics different from expected

**Solutions**:
1. Verify alignment penalties are being applied (check `fitness_breakdown()`)
2. Review operating region bounds - are they appropriate for your use case?
3. Check if data has expected characteristics (anomaly rate, shapes)
4. Consider adjusting thresholds if operational requirements differ
5. Document any legitimate violations (why they're acceptable)

## Continuous Validation

### During Development

- Run baseline verification after each evolution run
- Monitor fitness trends over generations
- Check metric distributions in population
- Validate against known-good rules

### In Production

- Periodic baseline verification
- Monitor fitness score distributions
- Track metric trends over time
- Alert on alignment drift indicators

## Related Documentation

- [`docs/FITNESS_ALIGNMENT.md`](FITNESS_ALIGNMENT.md): Comprehensive alignment documentation
- [`docs/FITNESS_ALIGNMENT_CHANGELOG.md`](FITNESS_ALIGNMENT_CHANGELOG.md): Historical changes to alignment
- [`tests/test_fitness.py`](../tests/test_fitness.py): Automated test cases
