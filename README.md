# Alert-Axolotl-Evo

A deterministic, interpretable genetic programming system for evolving symbolic alert rules. Alert-Axolotl-Evo uses evolutionary economics to discover and optimize anomaly detection rules expressed as explicit logic trees, ensuring full interpretability and deterministic behavior.

## Overview

Alert-Axolotl-Evo implements a **symbolic evolutionary economics** approach to program synthesis. Unlike neural networks or statistical learners, this system:

- Evolves **explicit logic trees** (nested tuples) that are fully inspectable
- Uses **economic constraints** to manage self-extension (PromotionManager)
- Maintains **deterministic behavior** through seeded evolution
- Enforces **causal contribution** requirements for learned primitives
- Provides **white-box interpretability** for all evolved rules

The system is designed for anomaly detection in time-series data, but the architecture supports any domain where symbolic rule evolution is valuable.

1. Load data (and labels/auto-label).
2. Generate initial population within depth limits.
3. Evaluate fitness with alignment penalties.
4. Select + mutate/crossover.
5. Track champions + checkpoint.
6. Optional: PromotionManager/Compiler macro promotion with budget enforcement.

## Determinism Contract

- **Python versions tested**: 3.8–3.11.
- **RNG sources**: Python's `random` module (seeded `random.Random` instances plus global seed). NumPy is optional and used only for deterministic percentile calculations during CSV auto-labeling (no RNG use). Tree visualization uses deterministic hashing to seed local RNGs.
- **Execution model**: Determinism assumes single-threaded execution and fixed evaluation ordering (no parallel evaluation or nondeterministic iteration sources).
- **Determinism statement**: Deterministic given the same Python version, dependencies, and single-threaded evaluation. Seed selection is controlled via `evolution.seed` in `config.yaml` or the `--seed` CLI flag.

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and design documentation
- **[docs/design_contract.md](docs/design_contract.md)**: Design Contract for AI Assistants - Evolutionary Economics architecture constraints
- **[docs/FITNESS_ALIGNMENT.md](docs/FITNESS_ALIGNMENT.md)**: Fitness alignment and metric-aligned semantic program synthesis documentation
- **[CHANGELOG.md](CHANGELOG.md)**: Version history and migration guide
- **[USAGE.md](USAGE.md)**: Practical usage guide and real-world examples
- **[META_EVOLUTION.md](META_EVOLUTION.md)**: Meta-evolution and self-improving system guide
- **[RESULTS.md](RESULTS.md)**: Meta-evolution experiment results and discoveries
- **[examples/fun_examples.md](examples/fun_examples.md)**: Fun gamification examples
- **[examples/output_sample.txt](examples/output_sample.txt)**: Sample evolution output

## Key Features

### Core Capabilities

- **Symbolic Rule Evolution**: Evolves explicit logic trees (not neural networks) for full interpretability
- **Production-Grade Fitness Alignment**: Metric-aligned semantic program synthesis ensures fitness scores correspond to operational value
  - Precision pressure (≥30% for human-paged alerts)
  - FPR penalties (≤15% operational noise tolerance)
  - Alert-rate bands (0.2%-20% deployment feasibility)
    - Defined per fitness evaluation pass over the dataset: `(TP+FP) / total evaluated rows` for a candidate rule. This is not per tick/window unless each row represents a tick/window in your dataset.
    - Config keys: `fitness_alignment.min_alert_rate` (default `0.002`) and `fitness_alignment.max_alert_rate` (default `0.20`).
  - Recall floors (≥10% minimum usefulness)
  - Degenerate collapse prevention (always-true/always-false elimination)
- **Evolutionary Economics**: PromotionManager enforces economic constraints on self-extension
  - Patterns must demonstrate causal lift to be promoted
  - Hard budget limits with eviction rules
  - Evidence-based promotion and pruning
- **Deterministic Behavior**: Seeded evolution ensures reproducible results
- **Real-World Data Support**: Load from CSV/JSON with optional auto-labeling
- **Self-Improving Mode**: System learns optimal configurations and discovers useful patterns
- **Checkpoint & Persistence**: Save/load evolution state and evolved rules

### Technical Highlights

- **Tree-based representation**: Programs are nested tuples like `('if_alert', ('>', ('avg', 'latency'), 100), 'High ping!')`
- **Fitness-based selection**: F-beta scoring with operational alignment constraints
- **Extensible architecture**: Easy to add new primitives and operators
- **Comprehensive configuration**: YAML/JSON config files with CLI overrides
- **Deployment-oriented**: Export evolved rules for integration into monitoring pipelines

## Installation

### Basic Installation

```bash
# Clone the repository
git clone <repository-url>
cd Alert-Axolotl-Evo

# Install in development mode
pip install -e .

# Or install with YAML support (for config files)
pip install -e ".[yaml]"
```


## Quick Start

### Try the Demo

```bash
# Run a quick 5-generation demo to see it in action!
python demo.py
```

This showcases the gamified evolution with fun names, champion battles, and funeral logs.

### Basic Usage

```bash
# Run with defaults
python -m alert_axolotl_evo.main

# Or use the CLI directly
alert-axolotl-evo
```

### With Configuration

```bash
# Use a config file
python -m alert_axolotl_evo.main --config config.yaml

# Override specific parameters
python -m alert_axolotl_evo.main --seed 123 --generations 50 --pop-size 100

# Use real data from CSV/JSON
python -m alert_axolotl_evo.main --data-source csv --data-path data.csv --value-column latency --anomaly-column is_anomaly
```

### Advanced Usage

```bash
# Save checkpoint during evolution
python -m alert_axolotl_evo.main --save-checkpoint checkpoint.json

# Resume from checkpoint
python -m alert_axolotl_evo.main --load-checkpoint checkpoint.json

# Export final champion rule
python -m alert_axolotl_evo.main --export-rule champion.json

# Meta-evolution: Evolve better evolution parameters
python -m alert_axolotl_evo.main --meta-evolve --meta-generations 5

# Self-improving mode with economic learning
python -m alert_axolotl_evo.main \
    --self-improving \
    --enable-promotion-manager \
    --library-budget 20 \
    --results-dir results/

# Generate performance report
python -m alert_axolotl_evo.main --performance-report
```

## Data Schema

When supplying CSV/JSON data via `--data-source` and `--data-path`, the dataset should include the following:

**Required fields**
- `timestamp`: time value (e.g., ISO 8601 string or epoch).
- One or more value columns (e.g., `latency`, `cpu`).
- Optional label/anomaly column if you have ground truth (e.g., `is_anomaly`).

**Optional fields**
- Entity identifiers (e.g., `host_id`, `service`).
- Grouping keys for segmented analysis (e.g., `region`, `tier`).

**Multivariate input**
- Provide multiple value columns (wide format), or a single `features`/`metrics` column containing a feature dictionary (JSON) per row.

**Tiny CSV example**
```csv
timestamp,latency,cpu,is_anomaly,host_id,region
2024-01-01T00:00:00Z,120.5,0.82,0,web-01,us-east
2024-01-01T00:01:00Z,300.0,0.95,1,web-01,us-east
```

## Configuration

### Complexity & Performance Notes

- **Default depth limits**: `evolution.max_depth` defaults to `7` (with `evolution.min_depth` default `2`). There is no explicit `evolution.max_nodes` cap in the config; tree size is instead controlled by depth limits plus the bloat penalty described below.
- **Bloat penalty**: `fitness.bloat_penalty` applies a linear penalty per node (fitness is reduced by `bloat_penalty * node_count`), so larger trees get proportionally lower scores.
- **Window function cost & safeguards**: `window_avg`, `window_max`, and `window_min` are more computationally expensive because they scan a rolling window per row. The fitness evaluator uses stratified sampling (early + late slices) to catch window-related invalid outputs early and rejects rules with excessive invalid outputs, reducing wasted work on expensive-but-invalid windowed trees.

### Configuration File (YAML)

Create a `config.yaml` file:

```yaml
evolution:
  seed: 42
  pop_size: 50
  generations: 40
  min_depth: 2
  max_depth: 7
  elite_ratio: 0.1

operators:
  crossover_rate: 0.9
  mutation_rate: 0.2
  tournament_size: 4

fitness:
  beta: 0.5
  bloat_penalty: 0.005
  fp_threshold: 40
  fp_penalty: 5.0

data:
  mock_size: 100
  anomaly_count: 8
  anomaly_multiplier: 2.5
```

### CLI Arguments

All configuration parameters can be overridden via CLI:

- `--seed`: Random seed
- `--pop-size`: Population size
- `--generations`: Number of generations
- `--min-depth`: Minimum tree depth
- `--max-depth`: Maximum tree depth
- `--crossover-rate`: Crossover probability
- `--mutation-rate`: Mutation probability
- `--tournament-size`: Tournament selection size

## Primitives

### Comparison Operators
- `>`, `<`, `>=`, `<=`, `==`, `!=`

### Logical Operators
- `and`, `or`, `not`

### Statistical Functions
- `avg`: Average
- `max`: Maximum
- `min`: Minimum
- `sum`: Sum
- `count`: Count
- `stddev`: Standard deviation
- `percentile`: Percentile (takes percentile as second argument; valid range is 0–100, not 0–1; uses default implementation with no interpolation)
- Example expression: `('>', ('percentile', 'latency', 95), 120)`

### Time-Window Functions
- `window_avg`: Rolling average
- `window_max`: Rolling maximum
- `window_min`: Rolling minimum

### Special Functions
- `if_alert`: Alert condition (if condition is true, return message)

### Terminals
- `"latency"`: Variable reference
- Numeric values: `25`, `50`, `75`, `100`, `150`, `200`
- Alert messages: `"High alert!"`, `"Danger zone!"`, etc.

### Rule Semantics
Comparisons only operate on numeric values; if either side is missing or non-numeric, the comparison returns `None` (not `False`). Logical operators do **not** use three-valued logic: `and`/`or` require boolean inputs, and `not` requires a boolean input—any `None` (or non-boolean) input makes the operator return `None` and short-circuits alerting. There is no default coercion for missing values; invalid semantics propagate `None` up the tree (e.g., `("and", (">", "latency", 100), (">", "missing_metric", 5))` ⇒ `None` because `"missing_metric"` is absent). 

## Examples

### Basic Evolution

```python
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config

config = Config()
evolve(config=config)
```

### Custom Configuration

```python
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config, EvolutionConfig

config = Config()
config.evolution.pop_size = 100
config.evolution.generations = 50
evolve(config=config)
```

### Save and Load Rules

```python
from alert_axolotl_evo.persistence import save_rule, load_rule
from pathlib import Path

# Save a rule
tree = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
save_rule(tree, fitness=8.5, generation=25, output_path=Path("rule.json"))

# Load a rule
rule_data = load_rule(Path("rule.json"))
print(rule_data["tree"])
print(rule_data["fitness"])
```

### Meta-Evolution: Evolving Better Evolution

```python
from alert_axolotl_evo.meta_evolution import MetaEvolver
from alert_axolotl_evo.config import Config

# Evolve optimal evolution parameters
base_config = Config()
meta_evolver = MetaEvolver(base_config=base_config, pop_size=10, generations=5)
best_genome = meta_evolver.evolve_configs()
optimal_config = best_genome.to_config(base_config)

# Use optimal config
evolve(config=optimal_config)
```

### Self-Improving Evolution with Economic Learning

```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.config import Config
from pathlib import Path

# Enable PromotionManager for economic learning
evolver = SelfImprovingEvolver(
    results_dir=Path("evolution_results"),
    enable_promotion_manager=True,  # Enable economic learning
    library_budget=20,              # Maximum active macros
    min_promo_batch=4,             # Minimum batch size
    promo_warmup_ticks=3,          # Warmup period
)

config = Config()

for i in range(10):
    config = evolver.get_optimal_config(config)
    result = evolver.run_and_learn(config, f"run_{i}")
    
    # View economic activity
    evolver.print_market_status()

# Get performance report
report = evolver.get_performance_report()
```

**Economic Learning Features:**
- **PromotionManager**: Enforces economic constraints on pattern promotion
  - Patterns must show incremental contribution (not just correlation)
  - Hard budget limits with eviction rules
  - Evidence-based promotion and pruning
- **Monotonic Economic Time**: `economy_tick` ensures correct pattern aging
- **Market Status Reports**: Inspect active library, promotions, and candidates

Incremental contribution is estimated via presence/absence statistics across champion batches (a complement method), not by ablating a macro from an otherwise identical individual. Promotions require a shrunken lift of at least 1.02 with 20+ observations, and market actions are gated by min-promo batch size and warmup ticks. Evidence validity checks can halt stats collection, and baseline failures close the market for that tick; stabilization is handled through shrinkage and minimum-evidence thresholds for pruning rather than explicit holdouts or slices.

See `docs/design_contract.md` for the complete economic architecture.

### Extending Primitives

```python
from alert_axolotl_evo.primitives import register_function, register_terminal

# Register a new function
register_function("multiply", lambda a, b: a * b, arity=2)

# Register a new terminal
register_terminal(300)
```

## Architecture

The system is organized into three main layers:

1. **Evolution Engine** (`evolution.py`, `fitness.py`, `operators.py`): Core GP mechanics
2. **Promotion/Market Layer** (`promotion.py`, `compiler.py`): Economic learning system
3. **Orchestration Layer** (`self_improving.py`): Coordinates evolution and promotion

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete architectural documentation.

### Project Structure

```
alert_axolotl_evo/
├── __init__.py
├── config.py              # Configuration management
├── primitives.py          # Function/terminal definitions
├── tree.py                # Tree utilities
├── evolution.py           # Evolution loop
├── fitness.py             # Fitness evaluation
├── operators.py           # Genetic operators
├── visualization.py       # ASCII trees, narratives
├── data.py                # Data loading (CSV/JSON/Mock)
├── persistence.py         # Save/load rules
├── analytics.py           # Performance analytics
├── pattern_discovery.py   # Pattern analysis
├── meta_evolution.py      # Meta-evolution core
├── self_improving.py      # Self-improving wrapper
├── promotion.py           # PromotionManager (economic learning)
├── compiler.py            # Macro compilation
└── main.py                # CLI entry point

tests/
├── test_tree.py
├── test_fitness.py
├── test_operators.py
├── test_evolution.py
├── test_data.py
├── test_data_provenance.py
├── test_csv_auto_labeling.py
├── test_economy_invariants.py
├── test_analytics.py
├── test_meta_evolution.py
└── test_self_improving.py
```

## Testing

Run the test suite:

```bash
pytest tests/
```

The test suite includes:
- Core functionality tests
- Economic invariant tests
- Data loading and provenance tests
- Integration tests

## API Reference

For detailed API documentation, see the inline docstrings in the source code. Key modules:

- **Core Evolution**: `evolution.evolve()`, `fitness.fitness()`, `fitness.evaluate()`
- **Data Loading**: `data.DataLoader`, `data.CSVDataLoader`, `data.JSONDataLoader`
- **Self-Improving**: `self_improving.SelfImprovingEvolver`
- **Economic Learning**: `promotion.PromotionManager`
- **Configuration**: `config.Config`

## Requirements

- Python 3.8 or higher
- Optional: PyYAML (for YAML config file support)

## Design Philosophy

Alert-Axolotl-Evo is built on four non-negotiable principles:

1. **Interpretability**: All evolved rules are explicit, inspectable logic trees
2. **Determinism**: Seeded runs are fully reproducible
3. **Evolutionary Economics**: Learning must pay rent - patterns must demonstrate causal value
4. **Fitness Alignment**: Fitness scores must correspond to operational value, not just numerical optimization

See [docs/design_contract.md](docs/design_contract.md) for the complete design contract and [docs/FITNESS_ALIGNMENT.md](docs/FITNESS_ALIGNMENT.md) for fitness alignment documentation.

## License

**Proprietary - All Rights Reserved**

Copyright (c) 2024 Alert Axolotl Evo

This software is proprietary and confidential. Unauthorized use, reproduction, or distribution is prohibited. For licensing inquiries, please contact the copyright holder.

See [LICENSE](LICENSE) for full terms.

## Acknowledgments

Built with principles from genetic programming, program synthesis, and evolutionary economics. The system demonstrates that interpretable AI can be both powerful and disciplined.
