# Alert-Axolotl-Evo

Deterministic genetic programming for evolving interpretable alert rules.

Instead of training a black-box anomaly detector, Alert-Axolotl-Evo evolves
explicit logic trees you can read, audit, and ship to production:

```python
("if_alert", (">", ("avg", "latency"), 100), "High ping!")
```

Fitness is tied to operational constraints (precision, false-positive rate,
alert rate), so "high fitness" means "useful on-call alert" — not a vanity
metric.

## Install

```bash
pip install -e .            # core
pip install -e ".[yaml]"    # with YAML config support
```

Requires Python 3.8+.

## Quick start

```bash
# Run with defaults (synthetic data, 40 generations)
alert-axolotl-evo

# From CSV
alert-axolotl-evo --data-source csv --data-path data.csv \
    --value-column latency --anomaly-column is_anomaly
```

Programmatic:

```python
from alert_axolotl_evo import Config, evolve

config = Config()
config.evolution.seed = 42
evolve(config=config)
```

See [examples/](examples/) for more.

## How it works

1. Load a time-series dataset (CSV, JSON, or synthetic).
2. Initialize a population of random logic trees.
3. Evaluate fitness against operational constraints.
4. Select → crossover → mutate; track champions; checkpoint.
5. Optionally promote useful sub-patterns into a macro library
   (see [docs/design-contract.md](docs/design-contract.md)).

## Why symbolic?

- **Interpretable** — every rule is a tree of explicit operators.
- **Deterministic** — seeded runs reproduce bit-for-bit (single-threaded).
- **Disciplined** — patterns must earn their place via causal lift, not correlation.

## Data schema

CSV or JSON with a single numeric value column and an optional anomaly label.
If the label column is missing in CSV, rows above the 98th percentile are
auto-labeled as anomalies.

```csv
timestamp,value,is_anomaly
2024-01-01T00:00:00Z,120.5,0
2024-01-01T00:01:00Z,300.0,1
```

## Documentation

- [Architecture](docs/architecture.md)
- [Usage guide](docs/usage.md)
- [Fitness alignment](docs/fitness-alignment.md)
- [Design contract](docs/design-contract.md)
- [Meta-evolution](docs/meta-evolution.md)
- [Experimental results](docs/results.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
pytest                  # run tests
ruff check .            # lint
```

## License

MIT — see [LICENSE](LICENSE).
