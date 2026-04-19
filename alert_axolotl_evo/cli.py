"""Command-line interface."""

import argparse
import json
from pathlib import Path

from alert_axolotl_evo.config import add_config_args, load_config, merge_cli_args
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.meta_evolution import MetaEvolver
from alert_axolotl_evo.self_improving import SelfImprovingEvolver


def main():
    parser = argparse.ArgumentParser(description="Alert-Axolotl-Evo: genetic programming for alert rules")
    parser = add_config_args(parser)
    parser.add_argument("--load-checkpoint", type=Path, help="Path to checkpoint file to resume from")
    parser.add_argument("--save-checkpoint", type=Path, help="Path to save checkpoint file")
    parser.add_argument("--export-rule", type=Path, help="Path to export final champion rule")
    parser.add_argument("--meta-evolve", action="store_true", help="Run meta-evolution to find optimal config")
    parser.add_argument("--meta-generations", type=int, default=5, help="Meta-evolution generations")
    parser.add_argument("--meta-pop-size", type=int, default=10, help="Meta-evolution population size")
    parser.add_argument("--self-improving", action="store_true", help="Use self-improving evolver")
    parser.add_argument("--results-dir", type=Path, default=Path("evolution_results"), help="Results directory for self-improving mode")
    parser.add_argument("--enable-promotion-manager", action="store_true", help="Enable PromotionManager (economic learning system)")
    parser.add_argument("--library-budget", type=int, default=50, help="Maximum number of active macros (PromotionManager)")
    parser.add_argument("--min-promo-batch", type=int, default=5, help="Minimum batch size to update market (PromotionManager)")
    parser.add_argument("--promo-warmup-ticks", type=int, default=2, help="Warmup ticks before promotions allowed (PromotionManager)")
    parser.add_argument("--performance-report", action="store_true", help="Generate performance report from results")
    
    args = parser.parse_args()
    
    # Performance report mode
    if args.performance_report:
        evolver = SelfImprovingEvolver(results_dir=args.results_dir)
        report = evolver.get_performance_report()
        print(json.dumps(report, indent=2))
        return
    
    # Load config from file if provided, otherwise use defaults
    if args.config:
        config = load_config(args.config)
    else:
        config = load_config()  # Will try to load config.yaml or return defaults
    
    # Merge CLI arguments into config
    config = merge_cli_args(config, args)
    
    # Meta-evolution mode
    if args.meta_evolve:
        print("Running meta-evolution to find optimal configuration...")
        meta_evolver = MetaEvolver(
            base_config=config,
            pop_size=args.meta_pop_size,
            generations=args.meta_generations,
        )
        best_genome = meta_evolver.evolve_configs()
        optimal_config = best_genome.to_config(config)
        print("\nOptimal configuration found:")
        print(f"  Population size: {best_genome.pop_size}")
        print(f"  Mutation rate: {best_genome.mutation_rate:.3f}")
        print(f"  Crossover rate: {best_genome.crossover_rate:.3f}")
        print(f"  Tournament size: {best_genome.tournament_size}")
        print(f"  Elite ratio: {best_genome.elite_ratio:.3f}")
        print("\nRunning evolution with optimal config...")
        config = optimal_config
    
    # Self-improving mode
    if args.self_improving:
        evolver = SelfImprovingEvolver(
            results_dir=args.results_dir,
            enable_promotion_manager=args.enable_promotion_manager,
            library_budget=args.library_budget,
            min_promo_batch=args.min_promo_batch,
            promo_warmup_ticks=args.promo_warmup_ticks,
        )
        # Use learned config if available
        config = evolver.get_optimal_config(config)
        run_id = f"run_{len(evolver.history)}"
        result = evolver.run_and_learn(config, run_id)
        print(f"\nRun complete. Fitness: {result['fitness']:.2f}")
        
        # Show market status if PromotionManager is enabled
        if args.enable_promotion_manager:
            evolver.print_market_status()
        
        suggestions = evolver.suggest_improvements()
        if suggestions:
            print("\nImprovement suggestions:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
        return
    
    # Standard evolution
    evolve(
        config=config,
        checkpoint_path=args.load_checkpoint,
        save_checkpoint_path=args.save_checkpoint,
        export_rule_path=args.export_rule,
    )


if __name__ == "__main__":
    main()

