# Archive Directory

This directory contains deprecated or historical versions of code.

## Files

### `alert_axolotl_evo.py`
- **Status**: Deprecated
- **Date Archived**: 2026-01-11
- **Reason**: Replaced by modular package structure in `alert_axolotl_evo/` directory
- **Replacement**: Use `alert_axolotl_evo_legacy.py` for backward compatibility, or the new modular package

This was the original single-file implementation of the genetic programming system. It has been replaced by a modular architecture with:
- Separate modules for configuration, data loading, fitness, operators, etc.
- Extended primitives (19 functions vs original 6)
- Real data integration (CSV/JSON)
- Persistence and checkpointing
- Comprehensive testing

The legacy wrapper `alert_axolotl_evo_legacy.py` in the root directory provides backward compatibility for scripts that import from the old file.

