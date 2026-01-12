# Changelog

All notable changes to Alert-Axolotl-Evo will be documented in this file.

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

