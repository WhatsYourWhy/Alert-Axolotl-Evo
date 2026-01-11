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

evolver = SelfImprovingEvolver()
config = Config()

# Each run improves the next
for i in range(5):
    config = evolver.get_optimal_config(config)
    result = evolver.run_and_learn(config, f"run_{i}")
    print(f"Run {i}: {result['fitness']:.2f}")

# Get suggestions
suggestions = evolver.suggest_improvements()
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

