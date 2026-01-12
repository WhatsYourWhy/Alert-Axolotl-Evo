"""Pattern discovery module for analyzing evolved rules and suggesting improvements."""

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from alert_axolotl_evo.persistence import load_rule
from alert_axolotl_evo.tree import node_count


def discover_common_patterns(rules_dir: Path) -> Dict[str, Any]:
    """
    Discover common patterns in evolved rules.
    
    Args:
        rules_dir: Directory containing rule JSON files
        
    Returns:
        Dictionary with discovered patterns
    """
    patterns = {
        "common_thresholds": Counter(),
        "common_functions": Counter(),
        "common_combinations": Counter(),
        "common_structures": Counter(),
    }
    
    # Only process champion files, not checkpoint files
    rule_files = [f for f in rules_dir.glob("*.json") if "champion" in f.name and "checkpoint" not in f.name]
    
    for rule_file in rule_files:
        try:
            rule_data = load_rule(rule_file)
            tree = rule_data["tree"]
            tree_str = str(tree)
            
            # Extract function usage
            for func in ["avg", "max", "min", "sum", "count", "stddev", "percentile", 
                        "window_avg", "window_max", "window_min", ">", "<", ">=", "<=", 
                        "==", "!=", "and", "or", "not", "if_alert"]:
                count = tree_str.count(f"'{func}'")
                if count > 0:
                    patterns["common_functions"][func] += count
            
            # Extract threshold values (numeric constants)
            thresholds = re.findall(r'\b(\d+)\b', tree_str)
            for t in thresholds:
                patterns["common_thresholds"][int(t)] += 1
            
            # Find common combinations
            if "'avg'" in tree_str and "'>'" in tree_str:
                patterns["common_combinations"]["avg+>"] += 1
            if "'avg'" in tree_str and "'<'" in tree_str:
                patterns["common_combinations"]["avg+<"] += 1
            if "'max'" in tree_str and "'>'" in tree_str:
                patterns["common_combinations"]["max+>"] += 1
            if "'and'" in tree_str and "'>'" in tree_str:
                patterns["common_combinations"]["and+>"] += 1
            if "'if_alert'" in tree_str and "'avg'" in tree_str:
                patterns["common_combinations"]["if_alert+avg"] += 1
            
            # Analyze structure
            complexity = node_count(tree)
            if complexity <= 3:
                patterns["common_structures"]["simple"] += 1
            elif complexity <= 7:
                patterns["common_structures"]["medium"] += 1
            else:
                patterns["common_structures"]["complex"] += 1
                
        except Exception:
            # Skip files that can't be processed (e.g., malformed JSON, missing fields)
            continue
    
    return patterns


def suggest_new_primitives(patterns: Dict[str, Any], min_usage: int = 5) -> List[str]:
    """
    Suggest new primitives based on discovered patterns.
    
    Args:
        patterns: Patterns from discover_common_patterns()
        min_usage: Minimum usage count to suggest
        
    Returns:
        List of suggestions for new primitives
    """
    suggestions = []
    
    # Check for common combinations that could be primitives
    combinations = patterns.get("common_combinations", Counter())
    
    if combinations.get("avg+>", 0) >= min_usage:
        suggestions.append("Consider adding 'avg_gt' primitive (avg + > combined)")
    
    if combinations.get("avg+<", 0) >= min_usage:
        suggestions.append("Consider adding 'avg_lt' primitive (avg + < combined)")
    
    if combinations.get("max+>", 0) >= min_usage:
        suggestions.append("Consider adding 'max_gt' primitive (max + > combined)")
    
    # Check for common threshold ranges
    thresholds = patterns.get("common_thresholds", Counter())
    if thresholds:
        common_thresholds = [t for t, count in thresholds.most_common(5) if count >= min_usage]
        if common_thresholds:
            suggestions.append(f"Common thresholds: {common_thresholds} - consider adding as terminal constants")
    
    return suggestions


def analyze_primitive_usage(rules_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    Analyze which primitives are most successful.
    
    Args:
        rules_dir: Directory containing rule JSON files
        
    Returns:
        Dictionary mapping primitives to usage statistics
    """
    primitive_stats = defaultdict(lambda: {
        "count": 0,
        "total_fitness": 0.0,
        "avg_fitness": 0.0,
        "max_fitness": 0.0,
    })
    
    for rule_file in rules_dir.glob("*.json"):
        try:
            rule_data = load_rule(rule_file)
            tree = rule_data["tree"]
            fitness = rule_data.get("fitness", 0.0)
            tree_str = str(tree)
            
            # Check each primitive
            primitives = ["avg", "max", "min", "sum", "count", "stddev", "percentile",
                         "window_avg", "window_max", "window_min", ">", "<", ">=", "<=",
                         "==", "!=", "and", "or", "not", "if_alert"]
            
            for prim in primitives:
                if f"'{prim}'" in tree_str:
                    stats = primitive_stats[prim]
                    stats["count"] += 1
                    stats["total_fitness"] += fitness
                    stats["max_fitness"] = max(stats["max_fitness"], fitness)
            
        except Exception:
            continue
    
    # Calculate averages
    for prim, stats in primitive_stats.items():
        if stats["count"] > 0:
            stats["avg_fitness"] = stats["total_fitness"] / stats["count"]
    
    return dict(primitive_stats)


def identify_optimization_targets(patterns: Dict[str, Any], 
                                  primitive_usage: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Identify code optimization opportunities based on usage patterns.
    
    Args:
        patterns: Patterns from discover_common_patterns()
        primitive_usage: Usage statistics from analyze_primitive_usage()
        
    Returns:
        List of optimization suggestions
    """
    suggestions = []
    
    # Find heavily used primitives that might need optimization
    for prim, stats in primitive_usage.items():
        if stats["count"] > 10 and stats["avg_fitness"] > 5.0:
            suggestions.append(f"'{prim}' is heavily used and successful - consider optimizing its implementation")
    
    # Check for unused primitives
    all_primitives = ["avg", "max", "min", "sum", "count", "stddev", "percentile",
                     "window_avg", "window_max", "window_min"]
    used_primitives = set(primitive_usage.keys())
    unused = set(all_primitives) - used_primitives
    if unused:
        suggestions.append(f"Unused primitives: {unused} - consider removing or improving them")
    
    # Check for complexity patterns
    structures = patterns.get("common_structures", Counter())
    if structures.get("complex", 0) > structures.get("simple", 0) * 2:
        suggestions.append("Complex rules dominate - consider stronger bloat control")
    
    return suggestions


def get_primitive_effectiveness(rules_dir: Path) -> Dict[str, float]:
    """
    Calculate effectiveness score for each primitive.
    
    Args:
        rules_dir: Directory containing rule JSON files
        
    Returns:
        Dictionary mapping primitives to effectiveness scores
    """
    primitive_usage = analyze_primitive_usage(rules_dir)
    effectiveness = {}
    
    for prim, stats in primitive_usage.items():
        if stats["count"] > 0:
            # Effectiveness = average fitness weighted by usage
            effectiveness[prim] = stats["avg_fitness"] * (1 + stats["count"] / 100)
    
    return effectiveness

