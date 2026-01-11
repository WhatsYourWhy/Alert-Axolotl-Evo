"""Demo script to showcase Alert Axolotl Evo in action."""

from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.config import Config
from pathlib import Path

def main():
    """Run a quick evolution demo."""
    print("=" * 70)
    print("  Alert Axolotl Evo - Evolution Demo")
    print("=" * 70)
    print("\nThis demo will run a short evolution (5 generations, 20 individuals)")
    print("to showcase the gamified genetic programming system.\n")
    print("Watch for:")
    print("  - Champion announcements with fun names")
    print("  - ASCII tree visualizations")
    print("  - Funeral logs for culled individuals")
    print("  - Fitness scores improving over generations")
    print("\n" + "=" * 70 + "\n")
    
    # Configure for quick demo
    config = Config()
    config.evolution.seed = 42  # Deterministic for reproducibility
    config.evolution.pop_size = 20  # Smaller population for faster demo
    config.evolution.generations = 5  # Just 5 generations for demo
    config.evolution.min_depth = 2
    config.evolution.max_depth = 5
    
    # Run evolution
    try:
        evolve(
            config=config,
            export_rule_path=Path("demo_champion.json")
        )
        
        print("\n" + "=" * 70)
        print("  Demo Complete!")
        print("=" * 70)
        print("\nThe evolved champion rule has been saved to: demo_champion.json")
        print("You can load it using:")
        print("  from alert_axolotl_evo.persistence import load_rule")
        print("  rule = load_rule(Path('demo_champion.json'))")
        print("\n")
        
    except KeyboardInterrupt:
        print("\n\nEvolution interrupted by user.")
    except Exception as e:
        print(f"\n\nError during evolution: {e}")
        raise

if __name__ == "__main__":
    main()

