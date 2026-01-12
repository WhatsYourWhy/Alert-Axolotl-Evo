# Design Contract: AI Assistants Working on Alert-Axolotl-Evo

This repository is an interpretable symbolic evolutionary system.
It is not deep learning. It does not optimize weights. It searches over program structure.

## Non-negotiable goals

### Interpretability

Output must remain inspectable as explicit rules/trees.

Do not introduce opaque representations or "learned weights."

### Determinism

Seeded runs must be replayable.

Avoid order-dependent randomness (registry ordering, dict iteration without sorting, time-based seeds).

### Evolutionary Economics ("Learning must pay rent")

The system may extend itself only under scarcity and causal contribution.

New primitives/macros must:

- show present vs absent advantage (causal proxy; not correlation),
- survive shrinkage / sample thresholds, and
- fit under a hard library budget with eviction rules.

Any "learning" mechanism that grows without eviction is a defect.

## Architecture boundaries (do not blur)

### Evolution Engine (evolution.py, fitness.py, core GP operators)

Must remain "pure": generates and evaluates candidates.

Must not silently learn or mutate registries mid-run (unless explicitly designed and documented).

### Promotion / Market Layer (promotion.py, compiler.py)

Enforces the economy: budget, lift, challenger, eviction.

Must compute absent stats via the complement method (Total − Present).

Must preserve visibility post-promotion via macro expansion (using introspection metadata).

### Orchestration Layer (self_improving.py)

Opt-in "Landlord" that coordinates evolution runs and applies promotion at safe boundaries.

Must not run competing learning systems in parallel.

## Required invariants (do not "simplify" these away)

### Core Economic Invariants

- **No unbudgeted learning**: All primitive registration must go through PromotionManager when enabled.
  - Legacy pattern discovery heuristics are disabled when PromotionManager is active.
  - No learning mechanism can grow without eviction constraints.

- **Learning must pay rent**: New primitives/macros must demonstrate causal contribution.
  - Must show present vs absent advantage (causal proxy, not correlation).
  - Must survive shrinkage and sample size thresholds.
  - Must fit under hard library budget with eviction rules.

- **Time always advances**: Economic time is monotonic and wall-clock based.
  - `economy_tick` represents "wall-clock runs" - increments on every run attempt.
  - This ensures ghost pruning works: patterns age even if runs are skipped (small batch, warmup, etc.).
  - The tick advances regardless of whether market updates occurred, so `(current_gen - last_seen_gen)` correctly measures pattern age.

- **Evidence before eviction**: Patterns cannot be evicted without sufficient evidence.
  - Ghost pruning requires minimum total observations (`MIN_EVIDENCE_FOR_GHOST`).
  - Harmful pruning requires minimum total observations (`MIN_EVIDENCE_FOR_HARM`).
  - This prevents premature eviction during sparse periods or low-sample chaos.

- **Environment repair ≠ learning**: Data preparation is not model learning.
  - Auto-labeling missing anomaly columns is environment repair (data preparation).
  - It happens before fitness evaluation and does not modify learning mechanisms.
  - It is inspectable and logged (provenance metadata).

### Technical Invariants

- Absent stats must not be computed by enumerating non-presence.
  - Use complement updates for performance and correct semantics.
- Promoted macros must remain analyzable.
  - Macro callables must carry subtree_definition (introspection hook).
- Pattern matching must inline-expand macro nodes before hashing.
- Budget enforcement is mandatory.
  - Library size is capped; eviction and challenger replacement are required.
- Promotion is reversible.
  - Underperforming or unused macros must be removable via unregister.

### Semantic Invariants

- **Root must be `if_alert`**: All evolved rules must have `if_alert` at root.
  - Enforced by `is_valid_alert_rule()` in `tree.py`.
  - Invalid trees return fitness -100.0.
- **Condition must evaluate to `bool` or invalid**: Conditions must return `bool`, not truthy values.
  - Type-strict evaluation: `type(x) is bool` not `bool(x)`.
  - Invalid conditions return `("__INVALID_CONDITION__", ...)` sentinel.
- **Message terminals cannot appear in conditions**: Message strings cannot be used as conditions.
  - Enforced by `is_boolean_expression()` in `tree.py`.
- **Invalid outputs > threshold (50%) ⇒ hard fail**: If invalid_rate > 0.5, return -100.0.
  - Soft penalty (0.5 * invalid_rate) applies below 50% threshold.
  - Enforced in `fitness()` function.

### Fitness Invariants

- **Champion must beat baselines (or warn/fail)**: Evolved champions must strictly dominate baselines.
  - Always-false, always-true, and random baselines must be beaten.
  - `print_fitness_comparison()` must warn if champion doesn't beat all baselines.
  - This is a critical sanity check for alignment.
- **Use `node_count` for bloat penalty**: Parsimony pressure via `bloat_penalty * node_count(tree)`.
  - Prevents unbounded tree growth.
  - Enforced in `fitness()` function.
- **Explicit penalties for always-true / never-alert**: Degenerate solutions must be penalized.
  - Always-true: Heavy penalty scaling with dataset size (lines 593-599).
  - Never-alert: Explicit -5.0 penalty (line 570).
  - Self-comparison: -10.0 penalty (line 566).
- **Baseline comparison must run and validate**: `print_fitness_comparison()` must be called.
  - Automatically called during evolution.
  - Can be called manually for validation.
- **Fitness function must be pure**: No side effects, no global state mutation.
  - `fitness()` must be deterministic and replayable.
  - Must not modify registries, learning mechanisms, or global state.

### Data Invariants

- **`consistent_data=True` means identical dataset across generations**: Same seed = same data.
  - When `consistent_data=True`, use `seed` (not `seed + gen`).
  - When `consistent_data=False`, use `seed + gen` (legacy behavior).
  - Enforced in `fitness()` and `fitness_breakdown()`.
- **Auto-labeling is "environment repair," must log provenance**: Data preparation is not learning.
  - Auto-labeling happens before fitness evaluation.
  - Must not modify learning mechanisms.
  - Must be inspectable and logged (provenance metadata).
- **Mock generator must produce known anomaly rate and shapes**: Mock data must be deterministic.
  - Anomaly count must match `data_config.anomaly_count`.
  - Anomaly multiplier must match `data_config.anomaly_multiplier`.
  - Seed determines exact anomaly positions.
- **Data loader output format must be validated**: Output must be `(List[float], List[bool])`.
  - Assertions in `fitness()` validate format.
  - Values must be numeric, anomalies must be boolean.
  - Lengths must match.

### Economy Invariants

- **PromotionManager is sole learning path when enabled**: No competing learning systems.
  - When `enable_promotion_manager=True`, legacy auto-register is disabled.
  - All primitive registration must go through PromotionManager.
  - No learning mechanism can grow without eviction constraints.
- **Monotonic economy tick semantics**: `economy_tick` always advances.
  - Represents "wall-clock runs" - increments on every run attempt.
  - Advances regardless of whether market updates occurred.
  - Enables correct ghost pruning (patterns age based on economic time).
- **Budget hard cap, challenger swap rules**: Library size is strictly capped.
  - Hard cap on active macros (default: 50, configurable via `library_budget`).
  - Challenger replacement when at budget (10% margin).
  - Eviction rules enforced (ghost pruning, harmful pruning).
- **Evidence floors for pruning**: Patterns cannot be evicted without sufficient evidence.
  - Ghost pruning requires `MIN_EVIDENCE_FOR_GHOST` total observations.
  - Harmful pruning requires `MIN_EVIDENCE_FOR_HARM` total observations.
  - Prevents premature eviction during sparse periods.

## Safe contribution checklist for AI edits

Before proposing code changes, verify:

- Does this change preserve deterministic behavior?
- Does it increase the primitive search space? If yes, where is the new constraint?
- Does it add learning? If yes, does it include budget + eviction + causal lift?
- Does it reduce explainability? If yes, it's out of scope.
