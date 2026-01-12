"""Self-improving evolution wrapper that learns from results."""

import json
from collections import Counter, defaultdict
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
    discover_structural_patterns,
    identify_optimization_targets,
    suggest_new_primitives,
)
from alert_axolotl_evo.visualization import (
    announce_pattern_discovery,
    display_pattern_leaderboard,
    generate_pattern_name,
    print_pattern_discovery_summary,
)
from alert_axolotl_evo.persistence import load_rule
from alert_axolotl_evo.primitives import FUNCTIONS, TERMINALS, register_function, register_terminal


class SelfImprovingEvolver:
    """Wrapper around evolution that learns from results and improves itself."""
    
    def __init__(
        self,
        results_dir: Path = Path("evolution_results"),
        auto_register: bool = True,
        adapt_data: bool = True,
        min_pattern_usage: int = 5,
    ):
        self.results_dir = results_dir
        self.results_dir.mkdir(exist_ok=True, parents=True)
        self.history: List[Dict[str, Any]] = []
        self.learned_config: Optional[Config] = None
        self.registered_primitives: List[str] = []
        self.data_adaptations: List[Dict[str, Any]] = []
        self.auto_register = auto_register
        self.adapt_data = adapt_data
        self.min_pattern_usage = min_pattern_usage
    
    def run_and_learn(self, config: Config, run_id: str) -> Dict[str, Any]:
        """
        Run evolution and learn from results.
        
        Args:
            config: Configuration to use
            run_id: Unique identifier for this run
            
        Returns:
            Result dictionary with fitness and metadata
        """
        # Auto-register primitives before evolution (if enabled and we have history)
        if self.auto_register and len(self.history) >= 2:
            registered = self.auto_register_primitives()
            if registered:
                # Track registered primitives
                self.registered_primitives.extend(registered)
        
        # Adapt data generation (if enabled)
        if self.adapt_data:
            adapted_config = self.adapt_data_generation(config)
        else:
            adapted_config = config
        
        # Run evolution with adapted config
        output_file = self.results_dir / f"{run_id}_champion.json"
        checkpoint_file = self.results_dir / f"checkpoint_{run_id}.json"
        
        evolve(
            config=adapted_config,
            export_rule_path=output_file,
            save_checkpoint_path=checkpoint_file,
        )
        
        # Analyze results
        result = load_rule(output_file)
        run_data = {
            "run_id": run_id,
            "config": adapted_config.to_dict(),
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
    
    def auto_register_primitives(self, min_usage: Optional[int] = None) -> List[str]:
        """
        Automatically register new primitives based on discovered patterns.
        
        Args:
            min_usage: Minimum pattern occurrence count to trigger registration
                      (defaults to self.min_pattern_usage)
        
        Returns:
            List of newly registered primitive names
        """
        if min_usage is None:
            min_usage = self.min_pattern_usage
        
        if not self.results_dir.exists():
            return []
        
        registered = []
        import logging
        logger = logging.getLogger("self_improving")
        
        try:
            # Use new structural pattern discovery
            patterns = discover_structural_patterns(self.results_dir)
            
            # Print discovery summary
            print_pattern_discovery_summary(patterns)
            
            # Get exact and abstract patterns
            exact_subtrees = patterns.get("exact_subtrees", Counter())
            abstract_algorithms = patterns.get("abstract_algorithms", Counter())
            hash_to_tree = patterns.get("hash_to_tree", {})
            subtree_metadata = patterns.get("subtree_metadata", {})
            
            # Register patterns based on exact matches (for now)
            # Future: implement promotion lifecycle (candidate -> probation -> permanent)
            for pattern_hash, count in exact_subtrees.items():
                if count >= min_usage and pattern_hash in hash_to_tree:
                    subtree = hash_to_tree[pattern_hash]
                    pattern_name = generate_pattern_name(pattern_hash, subtree)
                    
                    # Check if we should register this pattern
                    # For now, register common structural patterns as new primitives
                    # This is a simplified version - full implementation would use promotion lifecycle
                    
                    # Announce discovery if significant
                    if count >= min_usage:
                        metadata = subtree_metadata.get(pattern_hash, {})
                        avg_fitness = (metadata.get("fitness_sum", 0.0) / metadata.get("count", 1)) if metadata.get("count", 0) > 0 else 0.0
                        announce_pattern_discovery(pattern_hash, pattern_name, count, avg_fitness)
            
            # Also maintain backward compatibility with old combination-based registration
            combinations = patterns.get("common_combinations", {})
            combination_mappings = {
                "avg+>": ("avg_gt", lambda vals, threshold: sum(vals) / len(vals) > threshold if vals else False, 2),
                "avg+<": ("avg_lt", lambda vals, threshold: sum(vals) / len(vals) < threshold if vals else False, 2),
                "max+>": ("max_gt", lambda vals, threshold: max(vals) > threshold if vals else False, 2),
                "min+<": ("min_lt", lambda vals, threshold: min(vals) < threshold if vals else False, 2),
            }
            
            for pattern_key, (prim_name, func, arity) in combination_mappings.items():
                pattern_count = combinations.get(pattern_key, 0)
                if pattern_count >= min_usage and prim_name not in FUNCTIONS:
                    if prim_name not in self.registered_primitives:
                        register_function(prim_name, func, arity)
                        registered.append(prim_name)
                        logger.info("🎊 Auto-registered: %s", prim_name)
            
            # Register common thresholds as terminals
            thresholds = patterns.get("common_thresholds", {})
            if thresholds and hasattr(thresholds, 'most_common'):
                common_thresholds = [
                    (t, count) for t, count in thresholds.most_common(5)
                    if count >= min_usage
                ]
                for threshold, _ in common_thresholds:
                    if threshold not in TERMINALS:
                        if f"threshold_{threshold}" not in self.registered_primitives:
                            register_terminal(threshold)
                            registered.append(f"threshold_{threshold}")
            
            # Display leaderboard if we have patterns
            if exact_subtrees:
                display_pattern_leaderboard(patterns, top_n=5)
            
        except Exception as e:
            # Graceful degradation: if pattern discovery fails, return empty list
            logger.warning(f"Pattern discovery failed: {e}")
            return []
        
        return registered
    
    def adapt_data_generation(self, config: Config) -> Config:
        """
        Adapt data generation parameters based on learned patterns.
        
        Args:
            config: Configuration to adapt
            
        Returns:
            Modified config with adapted data parameters (original not mutated)
        """
        # Only adapt mock data, never modify real data configs
        if config.data.data_source != "mock":
            return config
        
        if not self.results_dir.exists() or len(self.history) < 2:
            return config
        
        # Create a copy to avoid mutating original
        import copy
        adapted_config = copy.deepcopy(config)
        
        try:
            patterns = discover_common_patterns(self.results_dir)
        except Exception:
            # Graceful degradation: if pattern discovery fails, return original config
            return config
        
        thresholds = patterns.get("common_thresholds", {})
        
        # Calculate fitness trend
        if len(self.history) >= 3:
            recent_fitness = [r["fitness"] for r in self.history[-3:]]
            fitness_trend = recent_fitness[-1] - recent_fitness[0]
        else:
            fitness_trend = 0
        
        # Calculate average complexity
        avg_complexity = sum(r["rule_complexity"] for r in self.history) / len(self.history)
        
        # Track what we're changing
        changes = {}
        
        # Adaptation 1: If thresholds are clustered, make anomalies closer to threshold
        if thresholds and hasattr(thresholds, 'most_common'):
            top_thresholds = [t for t, _ in thresholds.most_common(3)]
            if len(top_thresholds) >= 2:
                threshold_range = max(top_thresholds) - min(top_thresholds)
                if threshold_range < 50:  # Thresholds are clustered
                    # Reduce anomaly_multiplier by 10-15% to bring anomalies closer
                    reduction = 0.12  # 12% reduction
                    new_multiplier = adapted_config.data.anomaly_multiplier * (1 - reduction)
                    adapted_config.data.anomaly_multiplier = max(1.5, min(4.0, new_multiplier))  # Min 1.5x, Max 4.0x
                    changes["anomaly_multiplier"] = {
                        "old": config.data.anomaly_multiplier,
                        "new": adapted_config.data.anomaly_multiplier,
                        "reason": "Threshold clustering detected"
                    }
        
        # Adaptation 2: If rules are too simple, increase data complexity
        if avg_complexity < 5:
            # Increase mock_size by 10-20%
            increase = 0.15  # 15% increase
            new_size = int(adapted_config.data.mock_size * (1 + increase))
            adapted_config.data.mock_size = max(10, min(200, new_size))  # Min 10, Max 200
            changes["mock_size"] = {
                "old": config.data.mock_size,
                "new": adapted_config.data.mock_size,
                "reason": "Low rule complexity"
            }
        
        # Adaptation 3: If fitness is low, increase anomaly count
        if len(self.history) > 0:
            avg_fitness = sum(r["fitness"] for r in self.history) / len(self.history)
            if avg_fitness < 3.0:
                new_count = adapted_config.data.anomaly_count + 1
                adapted_config.data.anomaly_count = max(1, min(15, new_count))  # Min 1, Max 15
                changes["anomaly_count"] = {
                    "old": config.data.anomaly_count,
                    "new": adapted_config.data.anomaly_count,
                    "reason": "Low average fitness"
                }
        
        # Adaptation 4: If fitness is plateauing, increase difficulty
        if fitness_trend < 0.1 and len(self.history) >= 3:
            # Increase anomaly_multiplier by 5-10%
            increase = 0.075  # 7.5% increase
            new_multiplier = adapted_config.data.anomaly_multiplier * (1 + increase)
            adapted_config.data.anomaly_multiplier = max(1.5, min(4.0, new_multiplier))  # Min 1.5x, Max 4.0x
            if "anomaly_multiplier" not in changes:
                changes["anomaly_multiplier"] = {
                    "old": config.data.anomaly_multiplier,
                    "new": adapted_config.data.anomaly_multiplier,
                    "reason": "Fitness plateauing"
                }
            else:
                changes["anomaly_multiplier"]["reason"] += "; Fitness plateauing"
        
        # Final bounds check to ensure all values are within acceptable ranges
        adapted_config.data.anomaly_multiplier = max(1.5, min(4.0, adapted_config.data.anomaly_multiplier))
        adapted_config.data.mock_size = max(10, min(200, adapted_config.data.mock_size))
        adapted_config.data.anomaly_count = max(1, min(15, adapted_config.data.anomaly_count))
        
        # Track the adaptation
        if changes:
            self.data_adaptations.append({
                "run_id": len(self.history),
                "changes": changes,
            })
        
        return adapted_config
    
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
        
        # Convert Counter objects to serializable dicts
        top_functions = patterns.get("common_functions", {})
        top_combinations = patterns.get("common_combinations", {})
        
        # Convert config_performance keys to strings if needed
        serializable_config_perf = {}
        if config_performance:
            for k, v in config_performance.items():
                key = str(k) if not isinstance(k, (str, int, float, bool)) or k is None else k
                serializable_config_perf[key] = v
        
        report = {
            "metrics": metrics,
            "successful_configs": successful_configs,
            "config_performance": serializable_config_perf,
            "top_functions": dict(top_functions.most_common(5)) if hasattr(top_functions, 'most_common') else {},
            "top_combinations": {str(k): v for k, v in top_combinations.most_common(5)} if hasattr(top_combinations, 'most_common') else {},
            "primitive_effectiveness": {
                str(prim): stats["avg_fitness"] 
                for prim, stats in list(primitive_usage.items())[:10]
            },
            "suggestions": self.suggest_improvements(),
            "auto_registered_primitives": self.registered_primitives,
            "data_adaptations": self.data_adaptations[-5:],  # Last 5 adaptations
        }
        
        # Add pattern discovery statistics if available
        try:
            structural_patterns = discover_structural_patterns(self.results_dir)
            report["pattern_discovery"] = {
                "exact_patterns_count": len(structural_patterns.get("exact_subtrees", Counter())),
                "abstract_algorithms_count": len(structural_patterns.get("abstract_algorithms", Counter())),
                "total_unique_structures": len(structural_patterns.get("hash_to_tree", {})),
            }
        except Exception:
            # Pattern discovery not available
            pass
        
        return report

