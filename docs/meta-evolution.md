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

### Self-Improving (Legacy Mode)

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

### Self-Improving with Promotion Manager (Economic Learning)

The Promotion Manager implements "Evolutionary Economics" - a more rigorous learning system that enforces economic constraints on self-extension.

```python
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.config import Config

# Enable Promotion Manager (economic learning)
evolver = SelfImprovingEvolver(
    enable_promotion_manager=True,  # Enable economic learning
    library_budget=50,              # Maximum active macros
    # Note: When PM is enabled, legacy auto_register is automatically disabled
    # to prevent "economy leaks" (unbudgeted primitives)
)

config = Config()
config.evolution.pop_size = 30
config.evolution.generations = 10

# Run multiple evolutions - system discovers and promotes patterns
for i in range(5):
    result = evolver.run_and_learn(config, f"run_{i}")
    print(f"Run {i}: Fitness {result['fitness']:.2f}")
    
    # Check promotion activity
    report = evolver.get_performance_report()
    if "promotion_manager" in report:
        pm = report["promotion_manager"]
        print(f"  Active macros: {pm['active_macros_count']}/{pm['library_budget']}")
        print(f"  Promoted: {pm['promoted_macros']}")

# View economic activity
report = evolver.get_performance_report()
if "promotion_manager" in report:
    pm_stats = report["promotion_manager"]
    print(f"\nEconomic Summary:")
    print(f"  Active Macros: {pm_stats['active_macros_count']}")
    print(f"  Candidate Families: {pm_stats['candidate_families']}")
    print(f"  Total Promoted: {len(evolver.promoted_macros)}")
```

#### Economy Tick

The `economy_tick` is a monotonic counter that advances with each evolution run, independent of GP generation numbers. This provides a stable "market time" for tracking when patterns were last seen (for ghost pruning) and ensures economic operations happen at safe boundaries.

```python
# Economy tick starts at 0 and increments with each run
evolver = SelfImprovingEvolver(enable_promotion_manager=True)
assert evolver.economy_tick == 0

evolver.run_and_learn(config, "run_0")
assert evolver.economy_tick == 1

evolver.run_and_learn(config, "run_1")
assert evolver.economy_tick == 2  # Always increments
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
python -m alert_axolotl_evo --meta-evolve --meta-generations 5

# Self-improving mode
python -m alert_axolotl_evo --self-improving

# Performance report
python -m alert_axolotl_evo --performance-report
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

## Troubleshooting

### Auto-Registration Not Triggering

**Problem:** Auto-registration doesn't seem to be registering new primitives.

**Common Causes:**

1. **Threshold Too High:** The default `min_pattern_usage=5` requires a pattern to appear in at least 5 champion rules. If you only have a few runs, lower the threshold:
   ```python
   evolver = SelfImprovingEvolver(min_pattern_usage=2)  # Lower threshold
   ```

2. **Insufficient History:** Auto-registration requires at least 2 runs in history:
   ```python
   # Auto-registration only runs when len(evolver.history) >= 2
   # Run at least 2 evolution runs before expecting registration
   ```

3. **Patterns Not Common Enough:** The pattern must appear in multiple rules. Common patterns like "avg+>" need to be found in multiple champion files.

4. **Checkpoint Files:** Only champion files (with "champion" in filename) are analyzed. Checkpoint files are ignored.

**Diagnosis:**

Enable diagnostic logging to see what's happening:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

evolver = SelfImprovingEvolver(min_pattern_usage=1)
registered = evolver.auto_register_primitives()
```

The diagnostic output will show:
- How many files were analyzed
- Pattern counts found
- Which patterns meet the threshold
- Why registration did/didn't happen

**Solution:**

1. Lower the threshold for testing:
   ```python
   evolver = SelfImprovingEvolver(min_pattern_usage=1)
   ```

2. Run more evolution runs to accumulate more patterns

3. Check that champion files exist in the results directory:
   ```python
   champion_files = list(evolver.results_dir.glob("*champion*.json"))
   print(f"Found {len(champion_files)} champion files")
   ```

### Data Adaptation Not Working

**Problem:** Data parameters don't seem to be adapting.

**Common Causes:**

1. **Feature Disabled:** Check that `adapt_data=True`:
   ```python
   evolver = SelfImprovingEvolver(adapt_data=True)
   ```

2. **Insufficient History:** Requires at least 2 runs:
   ```python
   # Data adaptation needs len(evolver.history) >= 2
   ```

3. **Using Real Data:** Data adaptation only works with mock data. CSV/JSON data sources are never modified:
   ```python
   # Only adapts if config.data.data_source == "mock"
   ```

4. **Bounds Limiting Changes:** Adaptations are bounded (e.g., `anomaly_multiplier` between 1.5-4.0). If starting at an extreme value, changes may be clamped.

**Solution:**

1. Ensure you're using mock data:
   ```python
   config = Config()
   config.data.data_source = "mock"  # Required for adaptation
   ```

2. Run multiple runs to build history

3. Check adaptation history:
   ```python
   print(evolver.data_adaptations)  # See what changed
   ```

### Performance Issues

**Problem:** Pattern discovery is slow or system uses too much memory.

**Solutions:**

1. **Many Files:** Pattern discovery processes all champion files. If you have 100+ files, consider:
   - Cleaning up old results periodically
   - Using a separate results directory for each experiment

2. **Large History:** The history list grows with each run. For very long experiments:
   - The history is stored in memory (no automatic limit)
   - Consider periodically saving and clearing history if needed

3. **Pattern Discovery:** Should complete in < 1 second for 20 files. If slower:
   - Check for corrupted JSON files
   - Verify file system performance

### Common Error Messages

**"Error processing X.json: 'tree'"**
- The file is missing the 'tree' field (likely a checkpoint file)
- Solution: Only champion files are processed. This is expected for checkpoint files.

**"No thresholds found or thresholds is not a Counter"**
- Pattern discovery didn't find any numeric thresholds
- Solution: Normal if rules don't use numeric constants

**"Not registering 'X' (already in FUNCTIONS)"**
- The primitive is already registered (either built-in or previously auto-registered)
- Solution: This is expected behavior - primitives are only registered once

### Getting Help

If issues persist:

1. Enable diagnostic logging (see above)
2. Check the performance report:
   ```python
   report = evolver.get_performance_report()
   print(report)
   ```
3. Verify your setup matches the examples
4. Check that all required files exist and are readable
