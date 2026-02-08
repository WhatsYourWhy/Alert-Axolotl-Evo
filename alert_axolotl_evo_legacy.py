"""Legacy wrapper for backward compatibility.

This file maintains the original single-file interface for backward compatibility.
The new modular package is in the alert_axolotl_evo/ directory.
"""

from alert_axolotl_evo.evolution import evolve

if __name__ == "__main__":
    evolve(seed=42)

