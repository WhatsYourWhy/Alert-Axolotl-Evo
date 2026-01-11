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

### 3. Continuous Evolution with Checkpoints

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

## Troubleshooting

### Low Fitness Scores
- Check anomaly labels are correct
- Increase population size
- Run more generations
- Adjust fitness parameters in config

### Rules Too Complex
- Increase bloat penalty in config
- Reduce max_depth
- Add parsimony pressure

### No Improvement
- Increase mutation rate
- Check data quality
- Try different seeds
- Verify data loader is working

