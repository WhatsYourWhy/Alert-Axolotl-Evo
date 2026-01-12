# Alert-Axolotl-Evo Architecture

## Overview

Alert-Axolotl-Evo is a genetic programming system that evolves alert rules for anomaly detection. The system uses tree-based representations where programs are nested tuples, and evolves them through selection, crossover, and mutation.

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                      Main Entry Point                        │
│                    (main.py / CLI)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Layer                       │
│                    (config.py)                               │
│  - EvolutionConfig, OperatorsConfig, FitnessConfig          │
│  - DataConfig, Config (main container)                       │
│  - YAML/JSON loading, CLI argument parsing                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Evolution  │ │    Data      │ │  Persistence │
│   (evolution)│ │   (data.py)  │ │(persistence) │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │               │                 │
       │               │                 │
       ▼               ▼                 ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Operators  │ │   Fitness    │ │   Tree Utils │
│ (operators)  │ │  (fitness)   │ │   (tree)     │
└──────────────┘ └──────┬───────┘ └──────┬───────┘
                        │                 │
                        ▼                 ▼
                 ┌──────────────┐ ┌──────────────┐
                 │  Primitives  │ │ Visualization │
                 │ (primitives) │ │(visualization)│
                 └──────────────┘ └───────────────┘
```

### Module Responsibilities

#### `config.py`
- Configuration management with dataclass-based structures
- YAML/JSON file loading and parsing
- CLI argument integration and merging
- Default value management

#### `primitives.py`
- Function and terminal definitions
- Extensible registration system (`register_function`, `register_terminal`)
- 19 built-in functions:
  - Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
  - Logical: `and`, `or`, `not`
  - Statistical: `avg`, `max`, `min`, `sum`, `count`, `stddev`, `percentile`
  - Window: `window_avg`, `window_max`, `window_min`
- Arity mapping for validation

#### `tree.py`
- Tree manipulation utilities
- Hash generation for tree identification
- Node counting for parsimony pressure
- Subtree extraction and replacement for genetic operations
- Tree validation

#### `operators.py`
- Genetic operators: subtree crossover, point mutation
- Population initialization (Koza ramped half-and-half)
- Tournament selection
- Tree generation methods (grow and full)

#### `fitness.py`
- Tree evaluation engine (`evaluate`, `_evaluate`)
- Fitness calculation using F-beta score
- Data loader integration
- Number coercion utilities
- Mock data generation (fallback)

#### `data.py`
- Data loading abstraction (`DataLoader` base class)
- `MockDataLoader`: Deterministic mock data generation
- `CSVDataLoader`: Load from CSV files
- `JSONDataLoader`: Load from JSON files
- `TimeSeriesDataLoader`: Wrapper for time-series data
- Factory function: `create_data_loader()`

#### `evolution.py`
- Main evolution loop (`evolve()`)
- Population management
- Elite preservation
- Checkpoint integration
- Generation-by-generation progression

#### `visualization.py`
- ASCII tree rendering (`print_ascii_tree()`)
- Gamified narratives:
  - Birth announcements (`announce_birth()`)
  - Funeral logs (`log_funeral()`)
  - Champion displays
- Deterministic name generation (`generate_name()`)

#### `persistence.py`
- Rule export/import (`save_rule()`, `load_rule()`)
- Checkpoint save/load (`save_checkpoint()`, `load_checkpoint()`)
- Evolution state serialization (JSON format)

#### `main.py`
- CLI entry point
- Argument parsing with `argparse`
- Config loading and merging
- Integration of all components

## Data Flow

### Configuration Flow
```
CLI Arguments / Config File
    ↓
Config Object (dataclass)
    ↓
DataLoader Creation
    ↓
Evolution Parameters
```

### Evolution Flow
```
1. Configuration Load
   └─> Config object created from file/CLI

2. Data Loader Creation
   └─> DataLoader created based on config.data_source
       - MockDataLoader (default)
       - CSVDataLoader (if data_source="csv")
       - JSONDataLoader (if data_source="json")

3. Population Initialization
   └─> Ramped half-and-half initialization
       - Mix of grow and full methods
       - Depth range: min_depth to max_depth

4. Evolution Loop (per generation)
   ├─> Fitness Evaluation
   │   ├─> DataLoader.load() → (values, anomalies)
   │   ├─> For each tree:
   │   │   ├─> evaluate(tree, data) → result
   │   │   └─> Check alerting (isinstance(result, str))
   │   └─> Calculate TP/FP/FN → fitness score (F-beta)
   │
   ├─> Selection & Ranking
   │   └─> Sort by fitness (descending), then node count
   │
   ├─> Elite Preservation
   │   └─> Top 10% (configurable) preserved
   │
   ├─> Genetic Operations
   │   ├─> Tournament Selection (select parents)
   │   ├─> Subtree Crossover (90% rate, configurable)
   │   └─> Point Mutation (20% rate, configurable)
   │
   └─> Visualization & Logging
       ├─> Champion announcement
       ├─> Top 3 fitness display
       ├─> ASCII tree visualization
       └─> Funeral logs for culled individuals

5. Persistence (optional)
   ├─> Checkpoint saving (every generation if configured)
   └─> Rule export (final champion)
```

### Tree Evaluation Flow
```
Tree + Data Dictionary
    ↓
_evaluate() (recursive)
    ↓
Check node type:
    - Terminal → Return value or data lookup
    - Function → Evaluate children, apply function
    - if_alert → Evaluate condition, return message if true
    ↓
Result (number, boolean, string, or None)
```

## Tree Representation

Trees are nested tuples representing programs:

### Structure
- **Functions**: `(function_name, arg1, arg2, ...)`
- **Terminals**: `"latency"`, `100`, `"High alert!"`
- **Special**: `("if_alert", condition, message)`

### Example Tree
```python
("if_alert", 
  (">", 
    ("avg", "latency"), 
    100
  ), 
  "High alert!"
)
```

This represents: "If average latency > 100, alert 'High alert!'"

### Visual Representation
```
└─ if_alert
   ├─ >
   │  ├─ avg
   │  │  └─ latency
   │  └─ 100
   └─ High alert!
```

## Evolution Strategy

### Initialization
- **Method**: Ramped half-and-half (Koza)
- **Depth Range**: min_depth to max_depth (default: 2-7)
- **Distribution**: 50% grow method, 50% full method
- **Population Size**: Configurable (default: 50)

### Selection
- **Method**: Tournament selection
- **Tournament Size**: Configurable (default: 4)
- **Selection Pressure**: Higher fitness → higher probability

### Genetic Operators

#### Crossover
- **Type**: Subtree crossover
- **Rate**: 90% (configurable)
- **Process**: 
  1. Select random valid subtrees from both parents
  2. Swap subtrees
  3. Validate resulting trees
  4. If invalid, return parents unchanged

#### Mutation
- **Type**: Point mutation
- **Rate**: 20% per individual (configurable)
- **Process**:
  1. Select random subtree
  2. Replace with new random tree (grow method)
  3. Max depth: configurable (default: 2)

### Fitness Function
- **Metric**: F-beta score (beta=0.5, configurable)
- **Components**:
  - True Positives (TP): Anomaly detected correctly
  - False Positives (FP): Normal flagged as anomaly
  - False Negatives (FN): Anomaly missed
- **Bloat Control**: Penalty based on tree size
- **Bonuses**: Configurable bonuses for specific patterns

### Elitism
- **Ratio**: 10% (configurable)
- **Preservation**: Top performers survive to next generation

## Extension Points

### Adding New Primitives

```python
from alert_axolotl_evo.primitives import register_function, register_terminal

# Register a new function
register_function("multiply", lambda a, b: a * b, arity=2)

# Register a new terminal
register_terminal(300)
```

### Custom Data Loaders

```python
from alert_axolotl_evo.data import DataLoader
from typing import List, Tuple

class MyDataLoader(DataLoader):
    def load(self) -> Tuple[List[float], List[bool]]:
        # Your implementation
        values = [1.0, 2.0, 3.0]
        anomalies = [False, True, False]
        return values, anomalies
```

### Custom Fitness Functions

Modify `fitness()` in `fitness.py` or create a wrapper that calls it with custom parameters.

## Testing Strategy

### Unit Tests
- Each module has corresponding test file
- `test_tree.py`: Tree manipulation utilities
- `test_fitness.py`: Evaluation and fitness calculation
- `test_operators.py`: Genetic operators
- `test_evolution.py`: Evolution loop
- `test_data.py`: Data loaders

### Integration Tests
- Full evolution run with small parameters
- Deterministic behavior verification
- Checkpoint save/load
- Rule export/import

### Test Data
- Mock data generators
- Temporary CSV/JSON files for data loader tests
- Fixtures for common test scenarios

## Performance Considerations

### Bottlenecks
1. **Fitness Evaluation**: Called for every tree in every generation
   - Solution: Parallel evaluation (future enhancement)
2. **Tree Evaluation**: Recursive traversal
   - Solution: Memoization (future enhancement)
3. **Data Loading**: File I/O for CSV/JSON
   - Solution: Caching (future enhancement)

### Optimization Opportunities
- Parallel fitness evaluation using multiprocessing
- Tree evaluation caching for repeated subtrees
- DataLoader result caching
- Early termination for clearly unfit trees

## Configuration System

### Config File Format (YAML)
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
  data_source: mock  # "mock", "csv", or "json"
  data_path: null
  value_column: value
  timestamp_column: timestamp
  anomaly_column: null
  mock_size: 100
  anomaly_count: 8
  anomaly_multiplier: 2.5
```

### CLI Override
All config values can be overridden via CLI arguments.

## Persistence Format

### Rule Format (JSON)
```json
{
  "tree": ["if_alert", [">", ["avg", "latency"], 100], "High alert!"],
  "fitness": 8.5,
  "generation": 25,
  "metadata": {
    "hash": "abc123",
    "node_count": 5,
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Checkpoint Format (JSON)
```json
{
  "generation": 10,
  "seed": 42,
  "population": [...],
  "champion": [...],
  "champion_fitness": 8.5,
  "champion_history": [...],
  "config": {...},
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Meta-Evolution System

### Overview

The meta-evolution system creates a recursive self-improvement mechanism where the evolution process itself evolves to become better at evolving.

### Components

#### `analytics.py`
- **Performance Tracking**: Analyzes evolution results and tracks metrics
- **Config Analysis**: Identifies successful configurations
- **Convergence Analysis**: Measures how fast evolution converges

#### `pattern_discovery.py`
- **Pattern Analysis**: Discovers common patterns in evolved rules
- **Primitive Suggestions**: Suggests new primitives based on usage
- **Optimization Targets**: Identifies code optimization opportunities

#### `meta_evolution.py`
- **ConfigGenome**: Represents configuration as a genome
- **MetaEvolver**: Evolves better evolution parameters
- **Config Evaluation**: Tests configurations by running evolution

#### `self_improving.py`
- **SelfImprovingEvolver**: Wrapper that learns from each run
- **Automatic Tuning**: Adjusts config based on successful runs
- **Auto-Registration**: Automatically registers new primitives based on patterns
- **Data Adaptation**: Automatically adapts training data parameters
- **Improvement Suggestions**: Recommends system improvements
- **Performance Tracking**: Tracks registered primitives and data adaptations

### Meta-Evolution Flow

```
1. Initialize Meta-Evolution
   └─> Create population of ConfigGenomes

2. Meta-Evolution Loop
   ├─> Evaluate Each ConfigGenome
   │   └─> Run evolution with config → get fitness
   ├─> Select Best Configs
   ├─> Crossover & Mutate Configs
   └─> Next Generation

3. Use Best Config
   └─> Run actual evolution with optimal config
```

### Self-Improving Flow

```
1. Run Evolution
   └─> Save results to results_dir

2. Auto-Improve (before next run)
   ├─> Auto-Register Primitives
   │   ├─> Discover common patterns
   │   ├─> Register new function primitives (avg_gt, max_gt, etc.)
   │   └─> Register common threshold terminals
   ├─> Adapt Data Generation
   │   ├─> Analyze fitness trends and complexity
   │   ├─> Adjust mock data parameters conservatively
   │   └─> Track adaptations with reasons

3. Analyze Results
   ├─> Track performance metrics
   ├─> Identify successful configs
   └─> Discover patterns

4. Learn & Improve
   ├─> Update learned optimal config
   ├─> Generate improvement suggestions
   └─> Tune parameters automatically

5. Next Run
   └─> Use learned config and new primitives for better results
```

### Usage Example

```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.config import Config

evolver = SelfImprovingEvolver(
    auto_register=True,  # Enable auto-registration
    adapt_data=True,     # Enable data adaptation
)
config = Config()

# Run multiple times, learning each time
for i in range(5):
    config = evolver.get_optimal_config(config)  # Use learned config
    evolver.run_and_learn(config, f"run_{i}")     # Auto-improves before each run

# Check auto-improvements
print(f"Registered primitives: {evolver.registered_primitives}")
print(f"Data adaptations: {len(evolver.data_adaptations)}")

# Get suggestions
suggestions = evolver.suggest_improvements()

# Get performance report with auto-improvement history
report = evolver.get_performance_report()
```

## Future Enhancements

- Parallel fitness evaluation
- More sophisticated selection strategies (NSGA-II, etc.)
- Multi-objective optimization
- Interactive evolution visualization
- Rule validation and testing framework
- More statistical functions
- Time-series specific operators
- Rule explanation/interpretability
- Meta-evolution for fitness function parameters
- Automated primitive discovery and registration

