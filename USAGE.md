# Alert-Axolotl-Evo Usage Guide

## Quick Start

### Run the Demo

```bash
python demo.py
```

This runs a quick 5-generation evolution with 20 individuals, showcasing:
- Birth announcements with fun names
- Champion battles with fitness scores
- Funeral logs for culled individuals
- Evolution progression
- Final champion export

### Basic Usage

```bash
# Run with defaults (40 generations, 50 population)
python -m alert_axolotl_evo.main

# Quick test run
python -m alert_axolotl_evo.main --generations 5 --pop-size 20

# Custom seed for reproducibility
python -m alert_axolotl_evo.main --seed 123 --generations 10
```

## Real-World Implementation

### 1. Evolve Rules from Historical Data

```python
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config
from alert_axolotl_evo.persistence import load_rule
from pathlib import Path

# Configure for your data
config = Config()
config.data.data_source = "csv"  # or "json"
config.data.data_path = Path("your_data.csv")
config.data.value_column = "latency_ms"
config.data.anomaly_column = "is_anomaly"
config.evolution.generations = 50
config.evolution.pop_size = 100

# Evolve rules
evolve(
    config=config,
    export_rule_path=Path("best_rule.json")
)

# Load and use the evolved rule
rule_data = load_rule(Path("best_rule.json"))
champion_rule = rule_data["tree"]
fitness = rule_data["fitness"]

print(f"Evolved rule (fitness: {fitness}): {champion_rule}")
```

### 2. Use Evolved Rules in Production

```python
from alert_axolotl_evo.fitness import evaluate
from alert_axolotl_evo.persistence import load_rule
from pathlib import Path

# Load evolved rule
rule_data = load_rule(Path("best_rule.json"))
rule = rule_data["tree"]

# Check for alerts with current data
def check_alert(current_latency_values):
    """Use evolved rule to check for alerts."""
    data = {"latency": current_latency_values}
    result = evaluate(rule, data)
    
    if isinstance(result, str):
        # Alert triggered - result is the alert message
        return result
    return None  # No alert

# Example usage
current_window = [45.2, 48.1, 52.3, 125.8, 49.5]  # Last 5 latency values
alert = check_alert(current_window)
if alert:
    print(f"ALERT: {alert}")
    # Send to your monitoring system
```

### 3. Self-Improving Evolution with Economic Learning (Promotion Manager)

The Promotion Manager implements "Evolutionary Economics" - patterns must demonstrate causal value to be promoted as reusable macros. This system discovers common algorithm structures and promotes them through a lifecycle: candidate → active → retired.

#### Basic Usage

```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.config import Config
from pathlib import Path

# Enable Promotion Manager (economic learning system)
evolver = SelfImprovingEvolver(
    results_dir=Path("evolution_results"),
    enable_promotion_manager=True,  # Enable economic learning
    library_budget=50,              # Maximum active macros (default: 50)
)

config = Config()
config.evolution.pop_size = 30
config.evolution.generations = 10

# Run multiple evolutions - system learns and promotes patterns
for i in range(5):
    result = evolver.run_and_learn(config, f"run_{i}")
    print(f"Run {i+1}: Fitness {result['fitness']:.2f}")
    
    # Check promotion stats
    report = evolver.get_performance_report()
    if "promotion_manager" in report:
        pm_stats = report["promotion_manager"]
        print(f"  Active macros: {pm_stats['active_macros_count']}")
        print(f"  Promoted this run: {pm_stats['promoted_macros']}")
```

#### How It Works

1. **Pattern Discovery**: After each evolution, the system analyzes champions using Merkle hashing to find common subtrees
2. **Statistical Validation**: Patterns must show causal lift (better performance when present vs absent) with shrinkage to prevent overfitting
3. **Promotion**: High-performing patterns are compiled into 0-arity macros and registered
4. **Budget Enforcement**: System maintains a hard cap on active macros (default: 50)
5. **Pruning**: Unused macros (ghosts) and harmful macros are automatically retired

#### Configuration Options

```python
evolver = SelfImprovingEvolver(
    enable_promotion_manager=True,
    library_budget=20,              # Smaller budget for tighter control
    # Note: Legacy auto_register is automatically disabled when PM is enabled
    # to prevent "economy leaks" (unbudgeted primitives)
)
```

#### Viewing Economic Activity

```python
# Get performance report with promotion stats
report = evolver.get_performance_report()

if "promotion_manager" in report:
    pm = report["promotion_manager"]
    print(f"Active Macros: {pm['active_macros_count']}/{pm['library_budget']}")
    print(f"Promoted Macros: {pm['promoted_macros']}")
    print(f"Candidate Families: {pm['candidate_families']}")
```

#### Understanding the Economy

- **Economy Tick**: Monotonic counter that advances with each run (independent of GP generation)
- **Marginal Value**: Patterns must be at least 2% better than average to be promoted
- **Challenger Replacement**: New patterns must beat worst active by 10% margin to replace it
- **Ghost Pruning**: Macros unused for 15+ ticks are retired
- **Harmful Pruning**: Macros with lift < 0.99 are retired

See `ARCHITECTURE.md` for the complete design contract and economic model.

### 4. Continuous Evolution with Checkpoints

```python
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config
from pathlib import Path

config = Config()
config.evolution.generations = 100

# Run evolution with checkpointing
evolve(
    config=config,
    save_checkpoint_path=Path("checkpoint_gen50.json")
)

# Later, resume evolution
evolve(
    config=config,
    checkpoint_path=Path("checkpoint_gen50.json"),
    save_checkpoint_path=Path("checkpoint_gen100.json")
)
```

### 4. Integration with Monitoring Systems

```python
from alert_axolotl_evo.fitness import evaluate
from alert_axolotl_evo.persistence import load_rule
from pathlib import Path
import time

# Load production rule
rule = load_rule(Path("production_rule.json"))["tree"]

# Monitor in real-time
def monitor_loop(latency_stream):
    """Monitor latency stream using evolved rule."""
    window = []
    
    for value in latency_stream:
        window.append(value)
        if len(window) > 10:  # Keep last 10 values
            window = window[-10:]
        
        # Check for alert
        data = {"latency": window}
        result = evaluate(rule, data)
        
        if isinstance(result, str):
            send_alert(result, value)
            # Reset window after alert
            window = []
        
        time.sleep(1)  # Check every second
```

## Data Format Requirements

### CSV Format
```csv
value,timestamp,is_anomaly
45.2,2024-01-01T00:00:00,False
125.8,2024-01-01T00:03:00,True
49.5,2024-01-01T00:04:00,False
```

### JSON Format
```json
[
  {"value": 45.2, "timestamp": "2024-01-01T00:00:00", "is_anomaly": false},
  {"value": 125.8, "timestamp": "2024-01-01T00:03:00", "is_anomaly": true},
  {"value": 49.5, "timestamp": "2024-01-01T00:04:00", "is_anomaly": false}
]
```

## Configuration Examples

### High-Performance Run
```yaml
evolution:
  seed: 42
  pop_size: 200
  generations: 100
  min_depth: 2
  max_depth: 8

operators:
  crossover_rate: 0.9
  mutation_rate: 0.15
  tournament_size: 7
```

### Quick Experimentation
```yaml
evolution:
  pop_size: 30
  generations: 20

operators:
  mutation_rate: 0.3  # Higher mutation for exploration
```

## What You Get

### Evolved Rules
Rules are nested tuples that can be:
- Evaluated directly with `evaluate(rule, data)`
- Converted to your alert system format
- Exported/imported as JSON
- Visualized as ASCII trees

### Example Evolved Rules
```python
# Simple threshold rule
("if_alert", (">", ("avg", "latency"), 100), "High latency!")

# Complex statistical rule
("if_alert",
  (">", 
    ("percentile", "latency", 95),
    200
  ),
  "P95 spike detected!"
)

# Multi-condition rule
("if_alert",
  ("and",
    (">", ("avg", "latency"), 100),
    ("<", ("max", "latency"), 500)
  ),
  "Moderate anomaly"
)
```

## Tips for Best Results

1. **Data Quality**: Ensure your anomaly labels are accurate
2. **Population Size**: Larger populations (100+) for complex problems
3. **Generations**: More generations (50+) for better convergence
4. **Seed**: Use fixed seeds for reproducibility
5. **Checkpointing**: Save checkpoints for long runs
6. **Validation**: Test evolved rules on holdout data

## Meta-Evolution: Evolving Better Evolution

### What is Meta-Evolution?

Meta-evolution uses the evolution system itself to find optimal evolution parameters. It treats configurations (pop_size, mutation_rate, etc.) as genomes and evolves them.

### Basic Meta-Evolution

```python
from alert_axolotl_evo.meta_evolution import MetaEvolver
from alert_axolotl_evo.config import Config

base_config = Config()
meta_evolver = MetaEvolver(
    base_config=base_config,
    pop_size=10,  # Meta-population size
    generations=5,  # Meta-generations
    eval_generations=10,  # Generations per evaluation
)

# Evolve better config
best_genome = meta_evolver.evolve_configs()
optimal_config = best_genome.to_config(base_config)

# Use optimal config for actual evolution
from alert_axolotl_evo.evolution import evolve
evolve(config=optimal_config)
```

### Self-Improving Evolution

The self-improving wrapper learns from each run:

```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.config import Config

evolver = SelfImprovingEvolver(results_dir=Path("results"))
config = Config()

# Run multiple times - system learns and improves
for i in range(5):
    config = evolver.get_optimal_config(config)  # Gets learned optimal config
    result = evolver.run_and_learn(config, f"run_{i}")
    print(f"Run {i}: Fitness {result['fitness']:.2f}")

# Get improvement suggestions
suggestions = evolver.suggest_improvements()
for suggestion in suggestions:
    print(f"- {suggestion}")

# Get performance report
report = evolver.get_performance_report()
print(f"Average fitness: {report['metrics']['avg_fitness']:.2f}")
```

### Pattern Discovery

Analyze evolved rules to discover patterns:

```python
from alert_axolotl_evo.pattern_discovery import (
    discover_common_patterns,
    suggest_new_primitives,
    analyze_primitive_usage,
)

patterns = discover_common_patterns(Path("results"))
suggestions = suggest_new_primitives(patterns)
usage = analyze_primitive_usage(Path("results"))

print("Top functions:", patterns["common_functions"].most_common(5))
print("Suggestions:", suggestions)
```

### Analytics

Track and analyze evolution performance:

```python
from alert_axolotl_evo.analytics import (
    analyze_evolution_results,
    track_performance_metrics,
    identify_successful_configs,
)

results = analyze_evolution_results(Path("results"))
metrics = track_performance_metrics(results)
best_configs = identify_successful_configs(results, top_n=3)

print(f"Average fitness: {metrics['avg_fitness']:.2f}")
print(f"Best config: {best_configs[0]}")
```

## Troubleshooting

### Low Fitness Scores
- Check anomaly labels are correct
- Increase population size
- Run more generations
- Adjust fitness parameters in config
- Try meta-evolution to find optimal parameters

### Rules Too Complex
- Increase bloat penalty in config
- Reduce max_depth
- Add parsimony pressure

### No Improvement
- Increase mutation rate
- Check data quality
- Try different seeds
- Verify data loader is working
- Use meta-evolution to optimize parameters
- Use self-improving mode to learn from runs

