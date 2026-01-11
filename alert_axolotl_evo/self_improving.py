"""Self-improving evolution wrapper that learns from results."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from alert_axolotl_evo.analytics import (
    aggregate_config_performance,
    identify_successful_configs,
    track_performance_metrics,
)
from alert_axolotl_evo.config import Config
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.pattern_discovery import (
    analyze_primitive_usage,
    discover_common_patterns,
    identify_optimization_targets,
    suggest_new_primitives,
)
from alert_axolotl_evo.persistence import load_rule


class SelfImprovingEvolver:
    """Wrapper around evolution that learns from results and improves itself."""
    
    def __init__(self, results_dir: Path = Path("evolution_results")):
        self.results_dir = results_dir
        self.results_dir.mkdir(exist_ok=True, parents=True)
        self.history: List[Dict[str, Any]] = []
        self.learned_config: Optional[Config] = None
    
    def run_and_learn(self, config: Config, run_id: str) -> Dict[str, Any]:
        """
        Run evolution and learn from results.
        
        Args:
            config: Configuration to use
            run_id: Unique identifier for this run
            
        Returns:
            Result dictionary with fitness and metadata
        """
        # Run evolution
        output_file = self.results_dir / f"{run_id}_champion.json"
        checkpoint_file = self.results_dir / f"checkpoint_{run_id}.json"
        
        evolve(
            config=config,
            export_rule_path=output_file,
            save_checkpoint_path=checkpoint_file,
        )
        
        # Analyze results
        result = load_rule(output_file)
        run_data = {
            "run_id": run_id,
            "config": config.to_dict(),
            "fitness": result["fitness"],
            "generation": result["generation"],
            "rule_complexity": result["metadata"]["node_count"],
            "rule_hash": result["metadata"]["hash"],
        }
        
        self.history.append(run_data)
        
        # Learn from results
        self._update_learned_config()
        
        return run_data
    
    def _update_learned_config(self):
        """Update learned optimal configuration from history."""
        if len(self.history) < 2:
            return
        
        # Find best runs
        best_runs = sorted(self.history, key=lambda x: x["fitness"], reverse=True)[:3]
        
        if not best_runs:
            return
        
        # Average successful parameters
        avg_mutation = sum(
            r["config"]["operators"]["mutation_rate"] for r in best_runs
        ) / len(best_runs)
        
        avg_crossover = sum(
            r["config"]["operators"]["crossover_rate"] for r in best_runs
        ) / len(best_runs)
        
        avg_pop = int(
            sum(r["config"]["evolution"]["pop_size"] for r in best_runs) / len(best_runs)
        )
        
        avg_tournament = int(
            sum(r["config"]["operators"]["tournament_size"] for r in best_runs) / len(best_runs)
        )
        
        # Create learned config (blend with defaults)
        if self.learned_config is None:
            self.learned_config = Config()
        else:
            # Blend: 70% current learned, 30% new successful values
            self.learned_config.operators.mutation_rate = (
                self.learned_config.operators.mutation_rate * 0.7 + avg_mutation * 0.3
            )
            self.learned_config.operators.crossover_rate = (
                self.learned_config.operators.crossover_rate * 0.7 + avg_crossover * 0.3
            )
            self.learned_config.evolution.pop_size = int(
                self.learned_config.evolution.pop_size * 0.7 + avg_pop * 0.3
            )
            self.learned_config.operators.tournament_size = int(
                self.learned_config.operators.tournament_size * 0.7 + avg_tournament * 0.3
            )
    
    def suggest_improvements(self) -> List[str]:
        """
        Suggest code/system improvements based on evolved rules.
        
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        if not self.results_dir.exists():
            return suggestions
        
        # Analyze patterns
        patterns = discover_common_patterns(self.results_dir)
        primitive_usage = analyze_primitive_usage(self.results_dir)
        
        # Suggest new primitives
        primitive_suggestions = suggest_new_primitives(patterns)
        suggestions.extend(primitive_suggestions)
        
        # Identify optimizations
        optimization_suggestions = identify_optimization_targets(patterns, primitive_usage)
        suggestions.extend(optimization_suggestions)
        
        # Analyze performance
        from alert_axolotl_evo.analytics import analyze_evolution_results
        results = analyze_evolution_results(self.results_dir)
        metrics = track_performance_metrics(results)
        
        if metrics:
            if metrics.get("avg_fitness", 0) < 5.0:
                suggestions.append("Low average fitness - consider adjusting fitness function parameters")
            
            if metrics.get("avg_complexity", 0) > 10:
                suggestions.append("High rule complexity - consider increasing bloat penalty")
        
        return suggestions
    
    def get_optimal_config(self, base_config: Optional[Config] = None) -> Config:
        """
        Get the learned optimal configuration.
        
        Args:
            base_config: Base config to merge with (optional)
            
        Returns:
            Optimal configuration based on learning
        """
        if self.learned_config is None:
            return base_config or Config()
        
        if base_config is None:
            return self.learned_config
        
        # Merge with base config
        optimal = Config()
        optimal.evolution.seed = base_config.evolution.seed
        optimal.evolution.generations = base_config.evolution.generations
        optimal.evolution.min_depth = base_config.evolution.min_depth
        optimal.evolution.max_depth = base_config.evolution.max_depth
        optimal.fitness = base_config.fitness
        optimal.data = base_config.data
        
        # Use learned values for operators
        optimal.operators.mutation_rate = self.learned_config.operators.mutation_rate
        optimal.operators.crossover_rate = self.learned_config.operators.crossover_rate
        optimal.evolution.pop_size = self.learned_config.evolution.pop_size
        optimal.operators.tournament_size = self.learned_config.operators.tournament_size
        
        return optimal
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a performance report.
        
        Returns:
            Dictionary with performance metrics and insights
        """
        from alert_axolotl_evo.analytics import analyze_evolution_results
        
        if not self.results_dir.exists():
            return {"error": "No results directory found"}
        
        results = analyze_evolution_results(self.results_dir)
        metrics = track_performance_metrics(results)
        successful_configs = identify_successful_configs(results, top_n=3)
        config_performance = aggregate_config_performance(results)
        
        patterns = discover_common_patterns(self.results_dir)
        primitive_usage = analyze_primitive_usage(self.results_dir)
        
        report = {
            "metrics": metrics,
            "successful_configs": successful_configs,
            "config_performance": config_performance,
            "top_functions": dict(patterns.get("common_functions", {}).most_common(5)),
            "top_combinations": dict(patterns.get("common_combinations", {}).most_common(5)),
            "primitive_effectiveness": {
                prim: stats["avg_fitness"] 
                for prim, stats in list(primitive_usage.items())[:10]
            },
            "suggestions": self.suggest_improvements(),
        }
        
        return report

