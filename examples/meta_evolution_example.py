"""Example of meta-evolution: evolving better evolution parameters."""

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.meta_evolution import MetaEvolver

if __name__ == "__main__":
    print("=" * 70)
    print("Meta-Evolution Example")
    print("=" * 70)
    print("\nThis example uses evolution to evolve better evolution parameters!")
    print("The system will test different configurations and find optimal settings.\n")
    
    # Base configuration
    base_config = Config()
    base_config.evolution.generations = 10  # Quick evaluation
    base_config.evolution.seed = 42
    
    # Create meta-evolver
    meta_evolver = MetaEvolver(
        base_config=base_config,
        pop_size=8,  # Small meta-population
        generations=5,  # Few meta-generations for demo
        eval_generations=5,  # Quick evaluation
    )
    
    # Evolve configurations
    print("Starting meta-evolution...\n")
    best_genome = meta_evolver.evolve_configs()
    
    # Get optimal config
    optimal_config = meta_evolver.get_best_config()
    
    print("\n" + "=" * 70)
    print("Meta-Evolution Complete!")
    print("=" * 70)
    print(f"\nBest configuration found:")
    print(f"  Population size: {best_genome.pop_size}")
    print(f"  Mutation rate: {best_genome.mutation_rate:.3f}")
    print(f"  Crossover rate: {best_genome.crossover_rate:.3f}")
    print(f"  Tournament size: {best_genome.tournament_size}")
    print(f"  Elite ratio: {best_genome.elite_ratio:.3f}")
    print("\nYou can now use this configuration for better evolution results!")

