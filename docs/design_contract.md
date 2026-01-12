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

## Safe contribution checklist for AI edits

Before proposing code changes, verify:

- Does this change preserve deterministic behavior?
- Does it increase the primitive search space? If yes, where is the new constraint?
- Does it add learning? If yes, does it include budget + eviction + causal lift?
- Does it reduce explainability? If yes, it's out of scope.
