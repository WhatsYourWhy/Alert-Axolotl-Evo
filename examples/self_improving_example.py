"""Example of self-improving evolution system."""

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from pathlib import Path

if __name__ == "__main__":
    print("=" * 70)
    print("Self-Improving Evolution Example")
    print("=" * 70)
    print("\nThis example shows how the system learns from each run")
    print("and automatically improves its configuration.\n")
    
    # Create self-improving evolver
    results_dir = Path("self_improving_results")
    evolver = SelfImprovingEvolver(results_dir=results_dir)
    
    # Run multiple evolutions, learning from each
    base_config = Config()
    base_config.evolution.pop_size = 20
    base_config.evolution.generations = 5  # Quick runs for demo
    
    print("Running 3 evolution runs to demonstrate learning...\n")
    
    for i in range(3):
        print(f"\n--- Run {i+1} ---")
        
        # Get optimal config (learned from previous runs)
        config = evolver.get_optimal_config(base_config)
        
        if i > 0:
            print(f"Using learned config:")
            print(f"  Mutation rate: {config.operators.mutation_rate:.3f}")
            print(f"  Crossover rate: {config.operators.crossover_rate:.3f}")
            print(f"  Population size: {config.evolution.pop_size}")
        
        # Run evolution
        result = evolver.run_and_learn(config, f"demo_run_{i}")
        print(f"Fitness achieved: {result['fitness']:.2f}")
    
    # Show suggestions
    print("\n" + "=" * 70)
    print("Learning Complete!")
    print("=" * 70)
    
    suggestions = evolver.suggest_improvements()
    if suggestions:
        print("\nSystem suggestions for improvement:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
    
    # Show performance report
    print("\nPerformance Report:")
    report = evolver.get_performance_report()
    if "metrics" in report:
        metrics = report["metrics"]
        print(f"  Total runs: {metrics.get('total_runs', 0)}")
        print(f"  Average fitness: {metrics.get('avg_fitness', 0):.2f}")
        print(f"  Best fitness: {metrics.get('max_fitness', 0):.2f}")

