"""Analytics module for tracking and analyzing evolution performance."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from alert_axolotl_evo.persistence import load_checkpoint, load_rule


def analyze_evolution_results(results_dir: Path) -> List[Dict[str, Any]]:
    """
    Analyze evolution results from checkpoint and rule files.
    
    Args:
        results_dir: Directory containing checkpoint and rule JSON files
        
    Returns:
        List of analysis results for each evolution run
    """
    results = []
    
    # Analyze checkpoint files
    for checkpoint_file in results_dir.glob("checkpoint_*.json"):
        try:
            with open(checkpoint_file) as f:
                data = json.load(f)
                results.append({
                    "type": "checkpoint",
                    "file": checkpoint_file.name,
                    "generation": data.get("generation", 0),
                    "final_fitness": data.get("champion_fitness", 0.0),
                    "config": data.get("config", {}),
                    "convergence_gen": data.get("generation", 0),
                })
        except Exception as e:
            continue
    
    # Analyze rule files
    for rule_file in results_dir.glob("*_champion.json"):
        try:
            rule_data = load_rule(rule_file)
            results.append({
                "type": "rule",
                "file": rule_file.name,
                "fitness": rule_data.get("fitness", 0.0),
                "generation": rule_data.get("generation", 0),
                "complexity": rule_data.get("metadata", {}).get("node_count", 0),
            })
        except Exception:
            continue
    
    return results


def track_performance_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Track performance metrics from evolution results.
    
    Args:
        results: List of analysis results from analyze_evolution_results()
        
    Returns:
        Dictionary with performance metrics
    """
    if not results:
        return {}
    
    fitnesses = [r.get("fitness", r.get("final_fitness", 0.0)) for r in results]
    complexities = [r.get("complexity", 0) for r in results if "complexity" in r]
    generations = [r.get("generation", r.get("convergence_gen", 0)) for r in results]
    
    metrics = {
        "total_runs": len(results),
        "avg_fitness": sum(fitnesses) / len(fitnesses) if fitnesses else 0.0,
        "max_fitness": max(fitnesses) if fitnesses else 0.0,
        "min_fitness": min(fitnesses) if fitnesses else 0.0,
        "avg_complexity": sum(complexities) / len(complexities) if complexities else 0.0,
        "avg_generations": sum(generations) / len(generations) if generations else 0.0,
    }
    
    return metrics


def identify_successful_configs(results: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Identify the most successful configurations.
    
    Args:
        results: List of analysis results
        top_n: Number of top configs to return
        
    Returns:
        List of top performing configurations with their metrics
    """
    # Filter results with configs
    config_results = [r for r in results if "config" in r and r.get("config")]
    
    if not config_results:
        return []
    
    # Score each config by fitness
    scored_configs = []
    for result in config_results:
        fitness = result.get("fitness", result.get("final_fitness", 0.0))
        scored_configs.append({
            "config": result["config"],
            "fitness": fitness,
            "generation": result.get("generation", result.get("convergence_gen", 0)),
        })
    
    # Sort by fitness and return top N
    scored_configs.sort(key=lambda x: x["fitness"], reverse=True)
    return scored_configs[:top_n]


def calculate_convergence_rate(checkpoint_path: Path) -> Optional[float]:
    """
    Calculate convergence rate from checkpoint champion history.
    
    Args:
        checkpoint_path: Path to checkpoint file
        
    Returns:
        Convergence rate (fitness improvement per generation) or None
    """
    try:
        checkpoint = load_checkpoint(checkpoint_path)
        champion_history = checkpoint.get("champion_history", [])
        
        if len(champion_history) < 2:
            return None
        
        # Extract fitness values
        fitnesses = [fit for _, fit in champion_history]
        
        if len(fitnesses) < 2:
            return None
        
        # Calculate average improvement per generation
        improvements = [fitnesses[i] - fitnesses[i-1] for i in range(1, len(fitnesses))]
        return sum(improvements) / len(improvements) if improvements else None
        
    except Exception:
        return None


def aggregate_config_performance(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate performance metrics by configuration parameters.
    
    Args:
        results: List of analysis results
        
    Returns:
        Dictionary mapping config parameters to performance metrics
    """
    config_performance = defaultdict(lambda: {"fitnesses": [], "count": 0})
    
    for result in results:
        if "config" not in result or not result.get("config"):
            continue
        
        config = result["config"]
        fitness = result.get("fitness", result.get("final_fitness", 0.0))
        
        # Key by important parameters
        key = (
            config.get("evolution", {}).get("pop_size", 0),
            config.get("operators", {}).get("mutation_rate", 0.0),
            config.get("operators", {}).get("crossover_rate", 0.0),
        )
        
        config_performance[key]["fitnesses"].append(fitness)
        config_performance[key]["count"] += 1
    
    # Calculate averages
    aggregated = {}
    for key, data in config_performance.items():
        aggregated[key] = {
            "pop_size": key[0],
            "mutation_rate": key[1],
            "crossover_rate": key[2],
            "avg_fitness": sum(data["fitnesses"]) / len(data["fitnesses"]),
            "runs": data["count"],
        }
    
    return aggregated

