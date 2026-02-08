# Fitness Alignment Changelog

This document tracks changes to fitness alignment mechanisms over time, documenting what was added, when, and why.

## Version History

### Current State (2024)

**All alignment mechanisms active**:
- Precision pressure (≥30%)
- FPR penalties (≤15%)
- Alert-rate bands (0.2%-20%)
- Recall floors (≥10%)
- Degenerate collapse prevention
- Invalid output gates

**Status**: Production-ready. All mechanisms validated and working.

---

## Historical Evolution

### Phase 1: Basic F-Beta Scoring (Initial)

**State**: Simple F-beta scoring without alignment constraints.

**Issues**:
- Always-true rules dominated (high recall, but useless)
- Always-false rules sometimes won (zero false positives, but useless)
- Rules with terrible precision but high recall won

**Result**: System produced rules that looked good numerically but were operationally useless.

---

### Phase 2: Degenerate Collapse Prevention

**Added**: Penalties for degenerate solutions.

**Mechanisms**:
- Self-comparison detection (`is_self_comparison()`)
- No-alert penalty (tp=0, fp=0)

**Operational Justification**: Rules that always return True or always return False are useless, even if they technically have "good" metrics.

**Result**: Degenerate solutions eliminated, but precision issues remained.

**Code Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 433-438

---

### Phase 3: Alert-Rate Bands

**Added**: Constraints on alert rate to prevent never-firing and always-firing rules.

**Mechanisms**:
- Floor: <0.2% alert rate → penalty
- Ceiling: >20% alert rate → penalty
- Hard limit: >50% alert rate → heavy penalty (scales with dataset size)

**Operational Justification**: Rules must alert at deployment-feasible rates. Too low = never fires (useless). Too high = always fires (noisy).

**Result**: Rules became more deployment-feasible, but precision was still unconstrained.

**Code Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 755-769

---

### Phase 4: Precision Pressure

**Added**: Precision requirement (≥30%) to enforce human-paged alert cost models.

**Mechanism**:
- If precision < 0.3: penalty = 5.0 * (0.3 - precision)
- Max penalty: 1.5 points (for 0% precision)

**Operational Justification**: Human-paged alerts have real cost. If precision is too low, operators get overwhelmed by false alarms. 30% represents a reasonable balance.

**Result**: Rules started meeting operational precision requirements.

**Code Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 784-795

---

### Phase 5: FPR Penalties

**Added**: Direct FPR penalties (≤15%) to complement precision pressure.

**Mechanism**:
- If FPR > 0.15: penalty = 2.0 * (FPR - 0.15)
- Scales with excess FPR

**Operational Justification**: False positive rate directly impacts operational noise tolerance. Beyond 15%, alert fatigue sets in.

**Result**: Complete operational constraint coverage for false positives.

**Code Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 811-813

---

### Phase 6: Recall Floors

**Added**: Minimum detection requirements (≥10%) to ensure rules are useful.

**Mechanism**:
- If recall < 0.1 and tp == 0: penalty = 3.0

**Operational Justification**: Rules must detect at least some anomalies to be useful. Zero detection is worse than useless.

**Result**: Balanced alignment across all operational dimensions.

**Code Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 828-832

---

### Phase 7: Invalid Output Gates

**Added**: Hard and soft gates for invalid outputs.

**Mechanisms**:
- Hard gate: If invalid_rate > 0.5 → return -100.0 (reject tree)
- Soft penalty: If invalid_rate > 0.0 → penalty = 0.5 * invalid_rate

**Operational Justification**: Rules must produce valid outputs (string alert messages or None). Invalid outputs indicate broken logic.

**Result**: Semantic errors caught and penalized.

**Code Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 440-445

---

## Threshold Evolution

### Precision Threshold

- **Initial**: No threshold
- **Current**: 30% minimum
- **Justification**: Human-paged alert cost model
- **Future Considerations**: May need adjustment for automated response systems

### FPR Threshold

- **Initial**: No threshold
- **Current**: 15% maximum
- **Justification**: Operational noise tolerance
- **Future Considerations**: May vary by deployment context

### Alert Rate Bands

- **Initial**: No constraints
- **Current**: 0.2% floor, 20% ceiling, 50% hard limit
- **Justification**: Deployment feasibility
- **Future Considerations**: May need adjustment for different alert types

### Recall Floor

- **Initial**: No floor
- **Current**: 10% minimum (or TP > 0)
- **Justification**: Minimum usefulness
- **Future Considerations**: May need adjustment for rare anomaly detection

---

## Configuration Evolution

### Initial State

Alignment thresholds were hardcoded in the fitness function.

### Current State

`FitnessAlignmentConfig` dataclass added to [`alert_axolotl_evo/config.py`](alert_axolotl_evo/config.py), but thresholds still hardcoded in fitness function (future: use config).

**Future**: Integrate `FitnessAlignmentConfig` into fitness function to allow runtime threshold adjustment.

---

## Validation Evolution

### Initial State

No baseline verification.

### Current State

`print_fitness_comparison()` function validates alignment by comparing champions against baselines.

**Location**: [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) lines 840-1022

---

## Documentation Evolution

### Initial State

No alignment documentation.

### Current State

Comprehensive documentation:
- [`docs/FITNESS_ALIGNMENT.md`](FITNESS_ALIGNMENT.md): Main documentation
- [`docs/FITNESS_ALIGNMENT_VALIDATION.md`](FITNESS_ALIGNMENT_VALIDATION.md): Validation guide
- [`docs/FITNESS_ALIGNMENT_CHANGELOG.md`](FITNESS_ALIGNMENT_CHANGELOG.md): This file
- Code documentation in [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py)

---

## Lessons Learned

### What Worked

1. **Incremental Addition**: Adding mechanisms one at a time allowed validation at each step
2. **Operational Justification**: Each threshold has a clear operational story
3. **Baseline Verification**: Critical for catching alignment failures
4. **Degenerate Prevention**: Essential for preventing collapse

### What Didn't Work

1. **Initial Approach**: Simple F-beta without constraints → degenerate solutions
2. **Precision Alone**: Precision pressure without FPR penalties → unbalanced
3. **Hard Thresholds Only**: Needed soft penalties for gradient pressure

### Key Insights

1. **Alignment ≠ Optimization**: Making numbers bigger is not the goal
2. **Operational Constraints First**: Thresholds must map to real-world requirements
3. **Balance Matters**: All constraints must work together
4. **Validation is Critical**: Baseline comparison catches failures early

---

## Future Considerations

### Potential Enhancements

1. **Configurable Thresholds**: Use `FitnessAlignmentConfig` in fitness function
2. **Context-Aware Alignment**: Different thresholds for different alert types
3. **Multi-Objective Optimization**: Explicit trade-offs between metrics
4. **Adaptive Thresholds**: Learn optimal thresholds from data
5. **Domain-Specific Alignment**: Custom alignment for different domains

### Known Limitations

1. **Hardcoded Thresholds**: Currently hardcoded, not using config
2. **One-Size-Fits-All**: Same thresholds for all use cases
3. **Static Constraints**: Thresholds don't adapt to data characteristics

---

## Related Documentation

- [`docs/FITNESS_ALIGNMENT.md`](FITNESS_ALIGNMENT.md): Comprehensive alignment documentation
- [`docs/FITNESS_ALIGNMENT_VALIDATION.md`](FITNESS_ALIGNMENT_VALIDATION.md): Validation guide
- [`ARCHITECTURE.md`](../ARCHITECTURE.md): System architecture
- [`CHANGELOG.md`](../CHANGELOG.md): General project changelog
