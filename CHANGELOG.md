# Changelog

All notable changes to Alert-Axolotl-Evo will be documented in this file.

## [Unreleased] - Semantic Firewall & Evidence Validity System

### Added
- **Semantic Firewall**: Multi-layer validation system to prevent invalid trees from wasting compute
  - Structure validation: Purely syntactic checks (`is_valid_alert_rule()`, `is_boolean_expression()`) before evaluation
  - Early rejection: Stratified sampling (early + late slices) to catch trees that break after enough history
  - Hard gates: Invalid output detection (>50% invalid_rate = -100.0 fitness)
  - Comparison operator invariants: Strict bool/None return (never numeric)
  - Message validation: Message slot must be string (not numeric/boolean)
- **Baseline Comparison System**: Structured baseline verification with typed exceptions
  - `BaselineComparisonFailed(RuntimeError)`: Typed exception for baseline invariant violations
  - `baseline_passed`: First-class field in `evolve()` result and `SelfImprovingEvolver.history`
  - `enforce_baseline_comparison`: Configurable flag (default False for dev, True for CI/release)
  - Baseline definitions logged for debugging
- **Evidence Validity Tracking**: Comprehensive system to prevent learning from invalid evidence
  - `invalid_evaluation`: Semantic invalidity flag (invalid_rate > 0.5)
  - `exception_rate`: Separate tracking of actual exceptions during evaluation
  - `data_provenance`: Expanded metadata including full data config and `dataset_hash`
  - `dataset_hash`: SHA256 hash of actual data (rounded values + anomalies) for robust verification
  - `evidence_valid`: Boolean flag combining invalid_evaluation, exception_rate, and provenance_ok
  - Hard stop in `PromotionManager`: Invalid evidence prevents stats collection and market updates
- **Stratified Sampling for Early Rejection**: Improved early rejection to prevent false negatives
  - Samples both early slice (first 5%) and late slice (last 5%) of data
  - Prevents false negatives from head-only sampling (catches window functions that break late)
  - Deterministic and seeded for reproducibility

### Changed
- `fitness_breakdown()`: Now returns `exception_rate`, `invalid_evaluation`, and expanded `data_provenance`
- `evolve()`: Returns structured result dict with `baseline_passed`, `baseline_details`, `champion_breakdown`, `evidence_valid`
- `SelfImprovingEvolver.run_and_learn()`: Extracts baseline and evidence fields from evolution result, enforces baseline comparison if configured
- `SelfImprovingEvolver._process_promotion_manager()`: Implements hard stop for invalid evidence, treats baseline failure as "market closed" but allows stats if evidence valid
- `PromotionManager.process_generation_results()`: Accepts `evidence_valid` flag, returns early if False
- `print_fitness_comparison()`: Returns dict with `provenance_ok` flag, verifies `dataset_hash` matching across champion and baselines
- `FitnessConfig.enforce_baseline_comparison`: Default changed to `False` for development-friendly behavior
- `_call_standard_function()`: Comparison operators now enforce strict bool return type (defensive check)
- Documentation: Updated all line number references in `docs/FITNESS_ALIGNMENT.md` and `docs/FITNESS_ALIGNMENT_CHANGELOG.md` to match current code

### Fixed
- Unicode encoding issues in `tests/test_documentation.py`: All file reads now use `encoding='utf-8'`
- Test failures in `test_promotion_integration.py`: Added missing `Mock` import
- Test failures in `test_self_improving.py`: Fixed test expectations and added cleanup for test isolation
- Line number references in documentation: Updated to match current code locations

### Testing
- Added regression tests: `test_early_rejection_stratified_sampling`, `test_comparison_ops_return_bool_or_none`, `test_message_validation`
- All 214 tests passing
- Integration tests verified: Economic invariants, promotion manager workflow, data provenance

## [Unreleased] - Fitness Alignment Documentation

### Added
- **Fitness Alignment Documentation**: Comprehensive documentation of Metric-Aligned Semantic Program Synthesis
  - `docs/FITNESS_ALIGNMENT.md`: Main documentation covering alignment mechanisms, operational justifications, and layered audience content
  - `docs/FITNESS_ALIGNMENT_VALIDATION.md`: Validation methodology, baseline comparison, and drift detection guide
  - `docs/FITNESS_ALIGNMENT_CHANGELOG.md`: Historical tracking of alignment mechanism evolution
- **FitnessAlignmentConfig**: New configuration dataclass for alignment thresholds
  - `min_precision`: Minimum precision threshold (default 0.3 = 30%)
  - `max_fpr`: Maximum false positive rate (default 0.15 = 15%)
  - `min_alert_rate`: Minimum alert rate floor (default 0.002 = 0.2%)
  - `max_alert_rate`: Maximum alert rate ceiling (default 0.20 = 20%)
  - `always_true_threshold`: Hard limit for always-true detection (default 0.50 = 50%)
  - `min_recall`: Minimum recall floor (default 0.1 = 10%)
- **Enhanced Code Documentation**: 
  - Module-level docstring in `fitness.py` explaining alignment philosophy
  - Section headers organizing alignment mechanisms
  - Detailed docstrings for each alignment mechanism with operational justifications
  - Enhanced function docstrings with alignment context

### Changed
- `ARCHITECTURE.md`: Added "Fitness Alignment Layer" section documenting Layer 5 of the architecture
- `README.md`: Added fitness alignment to Key Features and Design Philosophy sections
- `alert_axolotl_evo/fitness.py`: Enhanced with comprehensive alignment documentation
- `alert_axolotl_evo/config.py`: Added `FitnessAlignmentConfig` dataclass (thresholds still hardcoded, config for future use)

### Documentation
- **Fitness Alignment Mechanisms Documented**:
  - Precision pressure (≥30% for human-paged alerts)
  - FPR penalties (≤15% operational noise tolerance)
  - Alert-rate bands (0.2%-20% deployment feasibility)
  - Recall floors (≥10% minimum usefulness)
  - Degenerate collapse prevention (always-true/always-false elimination)
  - Invalid output gates (semantic error detection)
- **Operational Justifications**: Each threshold documented with real-world operational reasoning
- **Baseline Verification**: Documented how `print_fitness_comparison()` validates alignment
- **Validation Guide**: Comprehensive guide for testing and validating alignment mechanisms

### Notes
- Alignment mechanisms were implemented incrementally over time (see `docs/FITNESS_ALIGNMENT_CHANGELOG.md`)
- Current implementation uses hardcoded thresholds; `FitnessAlignmentConfig` added for future integration
- All alignment mechanisms are production-ready and validated

## [1.3.0] - 2026-01-11

### Added
- **Promotion Manager V4**: Economic learning system with macro promotion lifecycle
  - `compiler.py`: `PrimitiveCompiler` class for compiling subtrees into 0-arity macros
  - `promotion.py`: `PromotionManager` class with V4 logic
  - **Pattern Discovery**: Uses Merkle hashing for structural pattern identification
  - **Family/Variant Model**: Groups patterns by normalized structure (family) and tracks specific instances (variants)
  - **Statistical Shrinkage**: Causal lift calculation with shrinkage (k=50) to prevent overfitting
  - **Complement Method**: O(P) efficient stats updates using Total - Present = Absent
  - **Budget Enforcement**: Hard cap on active macros (default: 50) with 10% challenger margin
  - **Pruning**: Removes ghosts (unused 15+ generations) and harmful macros (lift < 0.99)
  - **Introspection**: Macros expand via `subtree_definition` attribute for pattern discovery
  - **Economic Constraints**: Enforces "learning must pay rent" philosophy
- **Generic Function Dispatch**: Refactored `fitness.py` evaluator to support dynamic function registration
  - Replaced hardcoded if/elif chains with generic `FUNCTIONS` lookup
  - Supports context-aware macros via `needs_context` flag
  - Arity enforcement prevents malformed trees from silently failing
- **Enhanced Primitives System**:
  - `register_function()` now accepts `needs_context` parameter
  - `unregister_function()` for pruning underperformers
  - `FUNCTION_NAMES` maintains sorted order for determinism
- **SelfImprovingEvolver Integration**:
  - `enable_promotion_manager` flag to opt-in to economic learning
  - `library_budget` parameter to control macro limit
  - `economy_tick` monotonic counter for market timing
  - Legacy auto-register disabled when Promotion Manager enabled (prevents "economy leaks")
  - Promotion stats included in performance reports
- **Comprehensive Test Suite**:
  - `tests/test_compiler.py`: Unit tests for PrimitiveCompiler
  - `tests/test_promotion.py`: Unit tests for PromotionManager
  - `tests/test_primitives.py`: Tests for needs_context and unregister_function
  - `tests/test_promotion_integration.py`: End-to-end integration tests
  - Updated `tests/test_fitness.py`: Tests for generic dispatch and macro support
  - Updated `tests/test_self_improving.py`: Tests for Promotion Manager integration

### Changed
- `fitness.py`: Refactored `_evaluate()` to use generic function dispatch
  - All functions now go through `FUNCTIONS` registry lookup
  - Added `_call_standard_function()` helper for type coercion
  - Error returns changed from `0` to `None` (neutral failure)
  - Arity validation before function dispatch
- `primitives.py`: 
  - `register_function()` signature: added `needs_context: bool = False`
  - `FUNCTION_NAMES` is now sorted after each append (determinism)
  - Added `unregister_function()` for removing primitives
- `self_improving.py`:
  - Added `enable_promotion_manager` and `library_budget` parameters
  - Promotion Manager processes champions after each evolution run
  - Economy tick advances monotonically
  - Legacy auto-register path disabled when PM enabled

### Architecture
- **Separation of Concerns**: Promotion Manager operates at orchestration boundary, not within evolution engine
- **Introspection Mechanism**: Macros carry `subtree_definition` for expansion during pattern discovery
- **Economic Model**: Learning requires evidence of marginal value, competes under scarcity, remains removable
- **Determinism**: All operations remain seed-deterministic and replayable

### Backward Compatibility
- All existing code continues to work without changes
- Promotion Manager is opt-in (disabled by default)
- Legacy auto-register still works when Promotion Manager is disabled
- Generic dispatch maintains compatibility with all existing function types

## [1.2.0] - 2026-01-11

### Added
- **Auto-Registration of Primitives**: System automatically registers new function and terminal primitives based on discovered patterns
  - Registers common combinations like `avg_gt`, `avg_lt`, `max_gt`, `min_lt`
  - Registers frequently-used threshold values as terminal constants
  - New primitives become available for future evolution runs
- **Adaptive Data Generation**: System automatically adapts mock data parameters to improve training effectiveness
  - Adapts based on fitness trends, rule complexity, and threshold patterns
  - Conservative adjustments (max 20% change per run)
  - Only adapts mock data (never modifies real CSV/JSON data)
  - Tracks all adaptations with reasons
- **Configuration Options**: New parameters for `SelfImprovingEvolver`
  - `auto_register`: Enable/disable auto-registration (default: True)
  - `adapt_data`: Enable/disable data adaptation (default: True)
  - `min_pattern_usage`: Minimum pattern count to trigger registration (default: 5)
- **Enhanced Tracking**: System tracks auto-improvements
  - `registered_primitives`: List of auto-registered primitives
  - `data_adaptations`: History of data parameter changes with reasons
- **Enhanced Performance Reports**: Reports now include auto-improvement history
  - `auto_registered_primitives`: List of registered primitives
  - `data_adaptations`: Last 5 data adaptations with details

### Changed
- `SelfImprovingEvolver.__init__()`: Added optional parameters `auto_register`, `adapt_data`, `min_pattern_usage`
- `SelfImprovingEvolver.run_and_learn()`: Now automatically registers primitives and adapts data before evolution
- `SelfImprovingEvolver.get_performance_report()`: Includes new fields for auto-improvements

## [1.1.0] - 2026-01-11

### Added
- **Meta-Evolution System**: Evolve better evolution parameters automatically
  - `meta_evolution.py`: Evolves configurations as genomes
  - `ConfigGenome`: Represents configuration as evolvable genome
  - `MetaEvolver`: Evolves better evolution parameters
- **Self-Improving System**: System learns from each run
  - `self_improving.py`: Wrapper that learns and improves automatically
  - `SelfImprovingEvolver`: Tracks history and tunes config automatically
  - Improvement suggestions based on patterns
- **Analytics Module**: Track and analyze evolution performance
  - `analytics.py`: Performance metrics, config analysis, convergence tracking
  - Performance reports and insights
- **Pattern Discovery**: Analyze evolved rules for patterns
  - `pattern_discovery.py`: Discover common patterns, suggest primitives
  - Primitive usage analysis and effectiveness scoring
- **CLI Integration**: Meta-evolution and self-improving modes
  - `--meta-evolve`: Run meta-evolution to find optimal config
  - `--self-improving`: Use self-improving evolver
  - `--performance-report`: Generate performance analysis
- **Example Scripts**: 
  - `examples/meta_evolution_example.py`: Meta-evolution demo
  - `examples/self_improving_example.py`: Self-improving demo
- **Tests**: Comprehensive tests for new modules
  - `tests/test_analytics.py`
  - `tests/test_meta_evolution.py`
  - `tests/test_self_improving.py`

### Changed
- `main.py`: Added meta-evolution and self-improving CLI options
- `__init__.py`: Exported new meta-evolution modules

## [1.0.0] - 2026-01-11

### Added
- **Modular Architecture**: Complete refactoring from single-file to modular package structure
  - `config.py`: Configuration management with YAML/JSON support
  - `primitives.py`: Extensible primitive system
  - `tree.py`: Tree manipulation utilities
  - `operators.py`: Genetic operators (crossover, mutation, selection)
  - `fitness.py`: Fitness evaluation and tree evaluation
  - `data.py`: Data loading system (mock, CSV, JSON)
  - `evolution.py`: Main evolution loop
  - `visualization.py`: ASCII trees and gamified narratives
  - `persistence.py`: Save/load rules and checkpoints
  - `main.py`: CLI entry point

- **Extended Primitives**: Expanded from 6 to 19 functions
  - Comparison operators: `>=`, `<=`, `==`, `!=`
  - Logical operators: `not` (unary)
  - Statistical functions: `max`, `min`, `sum`, `count`, `stddev`, `percentile`
  - Time-window functions: `window_avg`, `window_max`, `window_min`

- **Configuration System**
  - YAML/JSON config file support
  - CLI argument parsing with config merging
  - Comprehensive parameter control

- **Real Data Integration**
  - `CSVDataLoader`: Load data from CSV files
  - `JSONDataLoader`: Load data from JSON files
  - `TimeSeriesDataLoader`: Wrapper for time-series data
  - Factory function for automatic loader selection

- **Persistence**
  - Rule export/import (JSON format)
  - Checkpoint save/load for evolution state
  - Resume evolution from checkpoints

- **Testing Infrastructure**
  - Comprehensive test suite with pytest
  - Unit tests for all modules
  - Integration tests for evolution loop
  - Data loader tests

- **Documentation**
  - Comprehensive README with examples
  - Architecture documentation
  - API documentation
  - Example scripts

- **Package Configuration**
  - `pyproject.toml` for modern Python packaging
  - Optional YAML support via extras

### Changed
- **Breaking**: Single-file `alert_axolotl_evo.py` replaced by modular package
  - Old file moved to `archive/`
  - `alert_axolotl_evo_legacy.py` provides backward compatibility wrapper
  - Migration: Use `from alert_axolotl_evo import evolve` instead of importing from file

- **Fitness Function**: Enhanced with configurable parameters
  - F-beta parameter configurable
  - Bloat penalty configurable
  - FP threshold and penalty configurable

- **Evolution Loop**: Enhanced with checkpoint support
  - Can save/load evolution state
  - Champion history tracking
  - Configurable elite ratio

### Migration Guide

#### From Single-File to Modular Package

**Old way:**
```python
import alert_axolotl_evo
alert_axolotl_evo.evolve(seed=42)
```

**New way:**
```python
from alert_axolotl_evo import evolve
from alert_axolotl_evo.config import Config

config = Config()
evolve(config=config)
```

**Or use legacy wrapper:**
```python
# alert_axolotl_evo_legacy.py maintains old interface
import alert_axolotl_evo_legacy
alert_axolotl_evo_legacy.evolve(seed=42)  # Still works!
```

#### Configuration

**Old way:** Hardcoded parameters in function calls

**New way:** Use config file or CLI arguments
```bash
python -m alert_axolotl_evo.main --config config.yaml
```

#### Data Loading

**Old way:** Only mock data

**New way:** Multiple data sources
```python
config = Config()
config.data.data_source = "csv"
config.data.data_path = Path("data.csv")
```

### Deprecated
- `alert_axolotl_evo.py` (original single-file) - moved to `archive/`
  - Use modular package or `alert_axolotl_evo_legacy.py` wrapper

### Fixed
- Tree node counting accuracy
- Unicode encoding issues in Windows console (handled gracefully)
- Data loader error handling

### Security
- Removed unsafe `eval()` usage in checkpoint loading
- Safe JSON serialization/deserialization

## [0.1.0] - Original Release

### Added
- Initial single-file implementation
- Basic genetic programming system
- 6 primitive functions
- Mock data generation
- Gamified narratives
- ASCII tree visualization

