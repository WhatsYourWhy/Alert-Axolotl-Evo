# Alert-Axolotl-Evo Architecture

## Design Contract: AI Assistants Working on Alert-Axolotl-Evo

This repository is an interpretable symbolic evolutionary system.
It is not deep learning. It does not optimize weights. It searches over program structure.

### Non-negotiable goals

**Interpretability**

Output must remain inspectable as explicit rules/trees.

Do not introduce opaque representations or "learned weights."

**Determinism**

Seeded runs must be replayable.

Avoid order-dependent randomness (registry ordering, dict iteration without sorting, time-based seeds).

**Evolutionary Economics ("Learning must pay rent")**

The system may extend itself only under scarcity and causal contribution.

New primitives/macros must:

- show present vs absent advantage (causal proxy; not correlation),
- survive shrinkage / sample thresholds, and
- fit under a hard library budget with eviction rules.

Any "learning" mechanism that grows without eviction is a defect.

### Architecture boundaries (do not blur)

**Evolution Engine** (evolution.py, fitness.py, core GP operators)

Must remain "pure": generates and evaluates candidates.

Must not silently learn or mutate registries mid-run (unless explicitly designed and documented).

**Promotion / Market Layer** (promotion.py, compiler.py)

Enforces the economy: budget, lift, challenger, eviction.

Must compute absent stats via the complement method (Total − Present).

Must preserve visibility post-promotion via macro expansion (using introspection metadata).

**Orchestration Layer** (self_improving.py)

Opt-in "Landlord" that coordinates evolution runs and applies promotion at safe boundaries.

Must not run competing learning systems in parallel.

### Required invariants (do not "simplify" these away)

- Absent stats must not be computed by enumerating non-presence.
  - Use complement updates for performance and correct semantics.
- Promoted macros must remain analyzable.
  - Macro callables must carry subtree_definition (introspection hook).
- Pattern matching must inline-expand macro nodes before hashing.
- Budget enforcement is mandatory.
  - Library size is capped; eviction and challenger replacement are required.
- Promotion is reversible.
  - Underperforming or unused macros must be removable via unregister.

### Safe contribution checklist for AI edits

Before proposing code changes, verify:

- Does this change preserve deterministic behavior?
- Does it increase the primitive search space? If yes, where is the new constraint?
- Does it add learning? If yes, does it include budget + eviction + causal lift?
- Does it reduce explainability? If yes, it's out of scope.

### Environment Repair vs Learning

**Critical Distinction**: Data preparation (environment repair) is not model learning.

- **Environment Repair**: Auto-labeling missing anomaly columns in CSV files is data preparation.
  - This happens before fitness evaluation
  - It synthesizes ground truth from raw data using percentile thresholds
  - It is inspectable and logged (provenance metadata)
  - It does not modify the model or learning mechanisms
  
- **Model Learning**: PromotionManager's macro promotion is actual learning.
  - This happens during evolution via economic constraints
  - It requires causal lift, evidence thresholds, and budget enforcement
  - It modifies the active primitive library
  - It is the only allowed learning mechanism when enabled

Auto-labeling is environment repair, not knowledge injection. It preserves the system's economic discipline.

### Economic Time Semantics

The system uses **monotonic economic time** (`economy_tick`) that is independent of GP generation numbers.

- **Semantics**: `economy_tick` represents "wall-clock runs" - it increments on every run attempt
- **Monotonicity**: The tick always advances, even if market updates are skipped (small batch, warmup period)
- **Purpose**: Enables correct ghost pruning - patterns age based on economic time, not GP generations
- **Implementation**: `economy_tick` is used as `current_gen` in PromotionManager for `last_seen_gen` tracking

This ensures that patterns not seen for N economic ticks are correctly identified as ghosts, regardless of whether those ticks were skipped due to batch-size guards or warmup periods.

### What PromotionManager Is Allowed To Change

**PromotionManager CAN modify:**
- `active_library`: Dictionary of promoted macros (subject to `LIBRARY_BUDGET`)
- Primitive registry: Register/unregister macro functions via `register_fn`/`unregister_fn`
- Pattern statistics: Track `present_count`, `absent_count`, fitness sums for pattern variants

**PromotionManager CANNOT modify:**
- Core GP operators (crossover, mutation, selection)
- Fitness function logic
- Tree evaluation semantics
- Base primitive registry (non-macro functions)
- Evolution loop structure

PromotionManager operates at the orchestration boundary, not within the evolution engine. It observes champions and promotes patterns, but does not interfere with the core GP mechanics.

### What NOT to Do

This system works because it is disciplined. Do not:

- Add neural networks or learned weights
- Cache "helpful" macros outside PromotionManager
- Persist learned primitives outside PromotionManager
- Auto-promote based on frequency alone (must show causal lift)
- "Improve" lift math without understanding economic semantics
- Bypass budget constraints for "useful" patterns
- Create learning mechanisms that grow without eviction

---

## 🧭 Architectural Intent & Constraints

**(Normative Design Contract)**

This section defines why Alert-Axolotl-Evo exists, what class of system it is, and what constraints are non-negotiable.

**Any contributor (human or AI) must treat this as a design contract, not a suggestion.**

### 1. System Identity

Alert-Axolotl-Evo is a **Symbolic Evolutionary System**, not a statistical learner.

- It operates on explicit logic trees, not opaque numeric weights
- It searches over program structure, not parameter space
- It improves via selection under constraints, not gradient descent

This places the system in the domain of:
- Genetic Programming (GP)
- Program Synthesis
- Symbolic Regression
- Interpretable / White-Box AI

**This system must remain inspectable, replayable, and explainable.**

If a change reduces explainability in exchange for performance, it is out of scope.

### 2. Core Philosophy: Learning Must Pay Rent

Alert-Axolotl-Evo is explicitly designed to avoid uncontrolled self-extension.

Every new behavior, rule, or primitive must:
- Demonstrate marginal causal value
- Compete under scarcity
- Remain removable

**There is no "free learning."**

This philosophy is enforced via:
- Family/Variant grouping
- Present-vs-Absent causal lift (not correlation)
- Shrinkage against small samples
- Hard library budget with eviction

Any proposal that adds learning capacity must also add a constraint.

### 3. What the System Is Allowed to Learn

**Allowed:**
- Reusable logic subtrees ("Macros")
  - Only when they:
    - are structurally identifiable
    - improve outcomes when present vs absent
    - survive competition under a fixed budget

**Not Allowed (by default):**
- Unbounded primitive growth
- Implicit or hidden state
- Opaque learned representations
- Accumulation without eviction
- Self-modification without auditability

The system may extend itself, but only in ways that:
- remain human-legible
- are reversible
- are attributable to specific evidence

### 4. Determinism Is a First-Class Constraint

This system is designed to be:
- Seed-deterministic
- Replayable
- Debuggable

**Design implications:**
- No hidden randomness
- No order-dependent registries
- No side effects during evaluation
- No learning that cannot be reproduced from recorded state

**If determinism conflicts with convenience, determinism wins.**

### 5. Separation of Concerns (Non-Negotiable)

The architecture is intentionally layered:

**Evolution Engine**
- Generates, mutates, and evaluates trees
- Has no memory
- Has no opinion about learning
- **Must remain pure**

**Promotion / Learning Layer**
- Observes results
- Computes causal contribution
- Decides what enters or leaves the library
- Enforces scarcity

**Orchestration Layer** (e.g. SelfImprovingEvolver)
- Opt-in only
- Coordinates evolution + promotion
- Owns persistence and lifecycle

**Evolution must not secretly learn.**
**Learning must not secretly mutate evolution.**

### 6. Why This Is Not Deep Learning

This system intentionally does not:
- approximate unknown functions via large matrices
- trade interpretability for scale
- generalize via latent representations

Instead, it:
- discovers explicit algorithms
- produces code, not weights
- favors clarity over raw accuracy

This makes it suitable for:
- regulated domains
- edge systems
- scientific hypothesis generation
- monitoring and alerting

### 7. Guardrails Against Search Space Explosion

Uncontrolled abstraction is the primary failure mode of symbolic systems.

This project explicitly prevents it via:
- Structural hashing (Merkle hashing of trees)
- Family/Variant separation
- Minimum complexity thresholds
- Hard library budget
- Challenger replacement rules
- Pruning of unused or harmful primitives

**Any change that weakens these guardrails must be justified explicitly.**

### 8. Guidance for AI Assistants

If you are an AI system assisting with this codebase:

**Do not optimize for:**
- elegance at the cost of explainability
- clever abstractions without constraints
- learning mechanisms without eviction

**Prefer:**
- explicit logic
- reversible changes
- conservative generalization

**Assume:**
- the biggest danger is false learning
- correlation is not causation
- growth without limits is failure

Your role is to help the system remain honest, not merely powerful.

### 9. Design Test (Litmus)

A proposed change is acceptable only if:

> "Can a future engineer remove this feature without breaking the system and understand exactly why it existed?"

If the answer is no, the change does not belong here.

### 10. Fitness Alignment

The system implements **Metric-Aligned Semantic Program Synthesis**, where fitness scores are aligned with operational constraints, not just optimized for higher numbers. This ensures that "high fitness" means "operationally useful" - meeting precision requirements, staying within false positive limits, and functioning within deployment constraints.

See [`docs/FITNESS_ALIGNMENT.md`](docs/FITNESS_ALIGNMENT.md) for comprehensive documentation of alignment mechanisms.

### 11. Summary

Alert-Axolotl-Evo is not trying to become everything.

It is trying to become **correct, interpretable, self-extending without losing control, and operationally aligned**.

**That constraint is the project.**

---

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
- Fitness calculation using F-beta score with operational alignment
- **Fitness Alignment**: Precision pressure, FPR penalties, alert-rate bands, recall floors, degenerate collapse prevention
- Baseline verification (`print_fitness_comparison()`)
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

6. Self-Improving Mode (optional, when --self-improving is used)
   ├─> Run evolution with SelfImprovingEvolver wrapper
   ├─> If PromotionManager enabled:
   │   ├─> Extract champions from checkpoint
   │   ├─> Update pattern statistics (process_generation_results)
   │   ├─> Promote/prune macros (promote_and_prune) after warmup
   │   └─> Increment economy_tick (monotonic economic time)
   └─> Learn optimal config from history
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

### Fitness Alignment Layer

Alert-Axolotl-Evo implements **Metric-Aligned Semantic Program Synthesis**, where the fitness function is aligned with real-world operational constraints rather than simply optimized for higher scores. This ensures that "high fitness" means "operationally useful," not just "numerically high."

**Key Alignment Mechanisms** (see [`docs/FITNESS_ALIGNMENT.md`](docs/FITNESS_ALIGNMENT.md) for details):

- **Precision Pressure** (≥30%): Enforces human-paged alert cost models
- **FPR Penalties** (≤15%): Operational noise tolerance limits
- **Alert-Rate Bands** (0.2%-20%): Deployment feasibility constraints
- **Recall Floors** (≥10%): Minimum usefulness requirements
- **Degenerate Collapse Prevention**: Eliminates always-true/always-false solutions
- **Invalid Output Gates**: Catches semantic errors in evolved logic

**Implementation**: All alignment mechanisms are in [`alert_axolotl_evo/fitness.py`](alert_axolotl_evo/fitness.py) (lines 540-669).

**Baseline Verification**: The system includes built-in baseline comparison (`print_fitness_comparison()`) to ensure evolved solutions strictly dominate degenerate baselines (always-true, always-false, random threshold).

**Architectural Position**: This is **Layer 5** of the five-layer architecture:
1. Genetic Programming (mechanism)
2. Program Synthesis (output form)
3. Constraint-Guided Search (semantic validity)
4. Economically Regulated Learning (macro library, budgets)
5. **Metric-Aligned Fitness Shaping** ← *This layer*

This layer is rare in genetic programming systems. Most stop at layers 1-2. Alert-Axolotl-Evo explicitly implements all five, with fitness alignment ensuring operational relevance.

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

