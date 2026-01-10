# Alert-Axolotl-Evo

Alert Axolotl Evo is a deterministic, gamified genetic programming system that evolves alert rules
expressed as nested tuples. It ships as a single, stdlib-only Python script that generates a
population of alert-rule trees, evaluates them against seeded mock latency data, and narrates an
over-the-top evolution loop with ASCII trees, dramatic logs, and playful names.

## What it does

- **Tree-based alert rules**: Programs are nested tuples like
  `('if_alert', ('>', ('avg', 'latency'), 100), 'High ping!')`.
- **Deterministic evolution**: Seeded data and selection ensure reproducible runs.
- **Gamified storytelling**: Births, battles, funerals, and champions are announced with flair.
- **Bloat-aware scoring**: Fitness rewards true positives, penalizes false positives, and lightly
  penalizes oversized trees.

## How to run

```bash
python alert_axolotl_evo.py
```

The script runs `evolve(seed=42)` by default, showing the champion tree each generation and ending
with a final narrative line about the surviving guardian.

## File overview

- `alert_axolotl_evo.py`: Full implementation of the evolver, including tree generation,
  evaluation, genetic operators, and narrative logging.
