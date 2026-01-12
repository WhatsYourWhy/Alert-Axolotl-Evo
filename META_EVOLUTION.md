# Meta-Evolution System

## Overview

The meta-evolution system creates a recursive self-improvement mechanism where Alert-Axolotl-Evo uses evolution to improve its own evolution process. This creates a feedback loop where the system gets better at getting better.

## How It Works

### 1. Meta-Evolution: Evolving Configurations

Instead of evolving alert rules, meta-evolution evolves **evolution parameters**:
- Population size
- Mutation rate
- Crossover rate
- Tournament size
- Elite ratio

These parameters are treated as a "genome" and evolved using the same genetic programming techniques.

### 2. Self-Improving: Learning from Runs

The self-improving wrapper tracks every evolution run and:
- Identifies successful configurations
- Averages successful parameters
- Automatically tunes future runs
- Suggests code improvements

### 3. Pattern Discovery: Analyzing Results

The system analyzes evolved rules to:
- Find common successful patterns
- Suggest new primitives based on usage
- Identify optimization opportunities
- Track primitive effectiveness

## Usage Examples

### Meta-Evolution

```python
from alert_axolotl_evo.meta_evolution import MetaEvolver
from alert_axolotl_evo.config import Config

# Evolve optimal parameters
base_config = Config()
meta_evolver = MetaEvolver(
    base_config=base_config,
    pop_size=10,  # Meta-population
    generations=5,  # Meta-generations
)

best_genome = meta_evolver.evolve_configs()
optimal_config = best_genome.to_config(base_config)

# Use optimal config
from alert_axolotl_evo.evolution import evolve
evolve(config=optimal_config)
```

### Self-Improving

```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver

evolver = SelfImprovingEvolver(
    auto_register=True,  # Enable automatic primitive registration
    adapt_data=True,     # Enable adaptive data generation
)
config = Config()

# Each run improves the next
for i in range(5):
    config = evolver.get_optimal_config(config)
    result = evolver.run_and_learn(config, f"run_{i}")
    print(f"Run {i}: {result['fitness']:.2f}")

# Get suggestions
suggestions = evolver.suggest_improvements()

# Check what was auto-registered
print(f"Auto-registered primitives: {evolver.registered_primitives}")

# Check data adaptations
print(f"Data adaptations: {evolver.data_adaptations}")
```

### Analytics

```python
from alert_axolotl_evo.analytics import analyze_evolution_results
from alert_axolotl_evo.pattern_discovery import discover_common_patterns

# Analyze results
results = analyze_evolution_results(Path("results"))
patterns = discover_common_patterns(Path("results"))

print("Top functions:", patterns["common_functions"].most_common(5))
```

## CLI Usage

```bash
# Meta-evolution mode
python -m alert_axolotl_evo.main --meta-evolve --meta-generations 5

# Self-improving mode
python -m alert_axolotl_evo.main --self-improving

# Performance report
python -m alert_axolotl_evo.main --performance-report
```

## Benefits

1. **Automatic Optimization**: System finds optimal parameters automatically
2. **Continuous Improvement**: Each run makes the next run better
3. **Pattern Discovery**: Identifies what works and suggests improvements
4. **Data-Driven**: Decisions based on actual performance data
5. **Recursive**: System improves itself recursively

## The Recursive Loop

```
Evolution Results
    ↓
Analytics & Pattern Discovery
    ↓
Identify Successful Patterns
    ↓
Evolve Better Configurations (Meta-Evolution)
    ↓
Use Optimal Config for Next Evolution
    ↓
Better Results
    ↓
(Repeat)
```

This creates a self-improving system that gets better over time!

## Auto-Registration and Data Adaptation

### Overview

The self-improving system now includes two powerful features that automatically improve the system itself:

1. **Auto-Registration**: Automatically registers new primitives (functions and terminals) based on discovered patterns
2. **Data Adaptation**: Automatically adapts training data parameters to create more challenging and effective datasets

### Auto-Registration of Primitives

When the system discovers common patterns in evolved rules, it can automatically register new primitives that combine frequently-used operations.

**How it works:**
- After 2+ runs, the system analyzes patterns in evolved rules
- If a pattern like "avg+>" appears frequently (default: 5+ times), it registers a new `avg_gt` primitive
- Common threshold values are registered as terminal constants
- New primitives become available for future evolution runs

**Example:**
```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver

evolver = SelfImprovingEvolver(
    auto_register=True,
    min_pattern_usage=5  # Minimum pattern count to trigger registration
)

# After running evolution multiple times with "avg+>" patterns:
# The system automatically registers "avg_gt" primitive
# This primitive is now available for future runs!
```

**Supported combinations:**
- `avg+>` → `avg_gt`: Average greater than threshold
- `avg+<` → `avg_lt`: Average less than threshold
- `max+>` → `max_gt`: Maximum greater than threshold
- `min+<` → `min_lt`: Minimum less than threshold

**Configuration:**
- `auto_register=True/False`: Enable/disable auto-registration (default: True)
- `min_pattern_usage`: Minimum pattern count to trigger registration (default: 5)

### Adaptive Data Generation

The system automatically adapts mock data generation parameters based on evolution results to create more effective training data.

**How it works:**
- Analyzes fitness trends, rule complexity, and threshold patterns
- Adapts data parameters conservatively (max 20% change per run)
- Only adapts mock data (never modifies real CSV/JSON data)
- Tracks all adaptations with reasons

**Adaptation strategies:**
1. **Threshold clustering**: If thresholds are clustered, reduces `anomaly_multiplier` to bring anomalies closer to thresholds (harder detection)
2. **Low complexity**: If rules are too simple, increases `mock_size` for more data points
3. **Low fitness**: If average fitness is low, increases `anomaly_count` for more anomalies to detect
4. **Fitness plateauing**: If fitness stops improving, increases `anomaly_multiplier` to increase difficulty

**Example:**
```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver

evolver = SelfImprovingEvolver(
    adapt_data=True  # Enable adaptive data generation
)

config = Config()
config.data.data_source = "mock"  # Only adapts mock data

# After running evolution:
# System adapts data parameters based on results
# Check adaptations:
for adaptation in evolver.data_adaptations:
    print(f"Run {adaptation['run_id']}:")
    for param, change in adaptation['changes'].items():
        print(f"  {param}: {change['old']} → {change['new']}")
        print(f"    Reason: {change['reason']}")
```

**Configuration:**
- `adapt_data=True/False`: Enable/disable data adaptation (default: True)
- Only works with `data_source="mock"` (real data is never modified)

### When Features Activate

Both features require some history to work:
- **Auto-registration**: Activates after 2+ runs (needs patterns to analyze)
- **Data adaptation**: Activates after 2+ runs (needs history to analyze trends)

### Performance Reports

The performance report now includes information about auto-improvements:

```python
report = evolver.get_performance_report()

# New fields:
print(f"Auto-registered primitives: {report['auto_registered_primitives']}")
print(f"Data adaptations: {report['data_adaptations']}")  # Last 5 adaptations
```

### Complete Example

```python
from alert_axolotl_evo.config import Config
from alert_axolotl_evo.self_improving import SelfImprovingEvolver

# Create evolver with all features enabled
evolver = SelfImprovingEvolver(
    auto_register=True,
    adapt_data=True,
    min_pattern_usage=5
)

config = Config()

# Run multiple evolutions
for i in range(5):
    config = evolver.get_optimal_config(config)
    result = evolver.run_and_learn(config, f"run_{i}")
    print(f"Run {i}: Fitness {result['fitness']:.2f}")

# Check what was improved
print(f"\nAuto-registered primitives: {evolver.registered_primitives}")
print(f"Data adaptations: {len(evolver.data_adaptations)}")

# Get full report
report = evolver.get_performance_report()
print(f"\nPerformance Report:")
print(f"  Best fitness: {report['metrics']['max_fitness']:.2f}")
print(f"  Primitives registered: {len(report['auto_registered_primitives'])}")
print(f"  Data adaptations: {len(report['data_adaptations'])}")
```

This creates a truly self-improving system that:
- Learns optimal parameters
- Discovers and registers new primitives
- Adapts training data for better results
- Gets better with each run!
