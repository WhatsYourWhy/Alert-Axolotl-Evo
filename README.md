# Alert-Axolotl-Evo

Alert Axolotl Evo is a deterministic, gamified genetic programming system that evolves alert rules expressed as nested tuples. It generates a population of alert-rule trees, evaluates them against data (mock or real), and narrates an over-the-top evolution loop with ASCII trees, dramatic logs, and playful names.

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and design documentation
- **[CHANGELOG.md](CHANGELOG.md)**: Version history and migration guide
- **[examples/fun_examples.md](examples/fun_examples.md)**: Fun gamification examples
- **[examples/output_sample.txt](examples/output_sample.txt)**: Sample evolution output

## Features

- **Tree-based alert rules**: Programs are nested tuples like `('if_alert', ('>', ('avg', 'latency'), 100), 'High ping!')`
- **Deterministic evolution**: Seeded data and selection ensure reproducible runs
- **Gamified storytelling**: Births, battles, funerals, and champions are announced with flair
- **Bloat-aware scoring**: Fitness rewards true positives, penalizes false positives, and lightly penalizes oversized trees
- **Extensible primitives**: Rich set of functions and operators, easily extensible
- **Configuration system**: YAML/JSON config files and CLI arguments
- **Persistence**: Save/load evolved rules and checkpoint evolution
- **Real data support**: Load data from CSV, JSON, or use mock data

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

### Requirements

- Python 3.8+
- Optional: PyYAML (for YAML config files)

## Quick Start

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
```

## Configuration

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
- `percentile`: Percentile (takes percentile as second argument)

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

### Extending Primitives

```python
from alert_axolotl_evo.primitives import register_function, register_terminal

# Register a new function
register_function("multiply", lambda a, b: a * b, arity=2)

# Register a new terminal
register_terminal(300)
```

## Project Structure

```
alert_axolotl_evo/
├── __init__.py
├── config.py              # Configuration management
├── primitives.py          # Function/terminal definitions
├── tree.py                # Tree utilities
├── evolution.py           # Evolution loop
├── fitness.py             # Fitness evaluation
├── operators.py           # Genetic operators
├── visualization.py        # ASCII trees, narratives
├── data.py                # Data loading
├── persistence.py         # Save/load rules
└── main.py                # Entry point

tests/
├── test_tree.py
├── test_fitness.py
├── test_operators.py
├── test_evolution.py
└── test_data.py
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## API Documentation

### Core Functions

#### `evolve(config, checkpoint_path, save_checkpoint_path, export_rule_path)`
Main evolution loop. Runs genetic programming to evolve alert rules.

#### `evaluate(tree, data)`
Evaluate a tree against data dictionary.

#### `fitness(tree, seed, gen, fitness_config, data_config)`
Calculate fitness score for a tree.

### Data Loaders

#### `MockDataLoader(seed, size, anomaly_count, anomaly_multiplier)`
Generate mock latency data with anomalies.

#### `CSVDataLoader(path, value_column, timestamp_column, anomaly_column)`
Load data from CSV file.

#### `JSONDataLoader(path, value_key, timestamp_key, anomaly_key)`
Load data from JSON file.

#### `create_data_loader(config)`
Factory function to create appropriate DataLoader from DataConfig.

## Archived Files

The original single-file implementation (`alert_axolotl_evo.py`) has been moved to the `archive/` directory. See `archive/README.md` for details. The new modular package is the recommended approach, but `alert_axolotl_evo_legacy.py` provides backward compatibility.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Acknowledgments

Inspired by genetic programming techniques and the joy of evolving code that actually works (sometimes).
