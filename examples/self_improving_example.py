"""Example of self-improving evolution system with auto-registration and data adaptation."""

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from pathlib import Path

if __name__ == "__main__":
    print("=" * 70)
    print("Self-Improving Evolution Example")
    print("=" * 70)
    print("\nThis example demonstrates:")
    print("  - Automatic learning from each run")
    print("  - Auto-registration of new primitives based on patterns")
    print("  - Adaptive data generation that improves training data")
    print("  - Configuration parameter optimization\n")
    
    # Create self-improving evolver with new features enabled
    results_dir = Path("self_improving_results")
    evolver = SelfImprovingEvolver(
        results_dir=results_dir,
        auto_register=True,      # Enable automatic primitive registration
        adapt_data=True,         # Enable adaptive data generation
        min_pattern_usage=3     # Lower threshold for demo (default is 5)
    )
    
    # Run multiple evolutions, learning from each
    base_config = Config()
    base_config.evolution.pop_size = 20
    base_config.evolution.generations = 5  # Quick runs for demo
    
    print("Running 4 evolution runs to demonstrate learning...\n")
    
    for i in range(4):
        print(f"\n{'='*70}")
        print(f"Run {i+1}")
        print(f"{'='*70}")
        
        # Get optimal config (learned from previous runs)
        config = evolver.get_optimal_config(base_config)
        
        # Show data parameters (will be adapted after run 2+)
        if i == 0:
            print(f"\nInitial data configuration:")
            print(f"  Mock size: {config.data.mock_size}")
            print(f"  Anomaly count: {config.data.anomaly_count}")
            print(f"  Anomaly multiplier: {config.data.anomaly_multiplier:.2f}")
        elif i > 1:
            print(f"\nAdapted data configuration:")
            print(f"  Mock size: {config.data.mock_size}")
            print(f"  Anomaly count: {config.data.anomaly_count}")
            print(f"  Anomaly multiplier: {config.data.anomaly_multiplier:.2f}")
            if evolver.data_adaptations:
                latest = evolver.data_adaptations[-1]
                print(f"  (Adapted based on: {latest.get('changes', {})})")
        
        if i > 0:
            print(f"\nUsing learned config:")
            print(f"  Mutation rate: {config.operators.mutation_rate:.3f}")
            print(f"  Crossover rate: {config.operators.crossover_rate:.3f}")
            print(f"  Population size: {config.evolution.pop_size}")
        
        # Run evolution (this will auto-register primitives and adapt data)
        result = evolver.run_and_learn(config, f"demo_run_{i}")
        print(f"\nFitness achieved: {result['fitness']:.2f}")
        print(f"Rule complexity: {result['rule_complexity']} nodes")
        
        # Show auto-registered primitives (after run 2+)
        if i >= 2 and evolver.registered_primitives:
            print(f"\nAuto-registered primitives: {evolver.registered_primitives}")
            print("  (New primitives discovered from patterns and registered)")
    
    # Show suggestions
    print("\n" + "=" * 70)
    print("Learning Complete!")
    print("=" * 70)
    
    suggestions = evolver.suggest_improvements()
    if suggestions:
        print("\nSystem suggestions for improvement:")
        for suggestion in suggestions:
            print(f"  - {suggestion}")
    
    # Show performance report with new fields
    print("\n" + "=" * 70)
    print("Performance Report")
    print("=" * 70)
    report = evolver.get_performance_report()
    if "metrics" in report:
        metrics = report["metrics"]
        print(f"\nMetrics:")
        print(f"  Total runs: {metrics.get('total_runs', 0)}")
        print(f"  Average fitness: {metrics.get('avg_fitness', 0):.2f}")
        print(f"  Best fitness: {metrics.get('max_fitness', 0):.2f}")
        print(f"  Average complexity: {metrics.get('avg_complexity', 0):.1f} nodes")
    
    # Show auto-registered primitives
    if report.get("auto_registered_primitives"):
        print(f"\nAuto-Registered Primitives:")
        for prim in report["auto_registered_primitives"]:
            print(f"  - {prim}")
    else:
        print(f"\nAuto-Registered Primitives: None (patterns may not have met threshold)")
    
    # Show data adaptations
    if report.get("data_adaptations"):
        print(f"\nData Adaptations (last 5):")
        for adaptation in report["data_adaptations"]:
            print(f"  Run {adaptation.get('run_id', '?')}:")
            for param, change_info in adaptation.get("changes", {}).items():
                print(f"    {param}: {change_info.get('old')} → {change_info.get('new')}")
                print(f"      Reason: {change_info.get('reason', 'N/A')}")
    else:
        print(f"\nData Adaptations: None")
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("\nThe system has:")
    print("  ✓ Learned optimal evolution parameters")
    if evolver.registered_primitives:
        print(f"  ✓ Auto-registered {len(evolver.registered_primitives)} new primitives")
    if evolver.data_adaptations:
        print(f"  ✓ Adapted data generation {len(evolver.data_adaptations)} times")
    print("  ✓ Improved its own configuration automatically")
    print("\nEach run makes the next run better!")

