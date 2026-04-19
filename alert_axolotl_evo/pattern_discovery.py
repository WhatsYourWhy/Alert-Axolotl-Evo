"""Pattern discovery module for analyzing evolved rules and suggesting improvements."""

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from alert_axolotl_evo.persistence import load_rule
from alert_axolotl_evo.primitives import TERMINALS
from alert_axolotl_evo.tree import merkle_hash, node_count, normalize_tree_structure


def extract_subtrees(node: Any, subtrees: Optional[List] = None, min_nodes: int = 2) -> List:
    """
    Recursively collect all subtree tuples with at least min_nodes.
    
    Args:
        node: Tree node (tuple, list, or terminal)
        subtrees: Accumulator list (created automatically if None)
        min_nodes: Minimum node count to include (default: 2)
        
    Returns:
        List of normalized subtree tuples
    """
    if subtrees is None:
        subtrees = []
    
    # Only add function nodes (tuples) with sufficient complexity
    if isinstance(node, (tuple, list)):
        normalized = normalize_tree_structure(node)
        if node_count(normalized) >= min_nodes:
            subtrees.append(normalized)
        
        # Recurse on children
        for child in node[1:]:
            extract_subtrees(child, subtrees, min_nodes)
    
    return subtrees


def discover_structural_patterns(rules_dir: Path) -> Dict[str, Any]:
    """
    Discover patterns using structural Merkle hashing.
    
    This function uses Merkle hashing to find exact structural duplicates
    and abstract algorithm patterns (with variable normalization).
    
    Args:
        rules_dir: Directory containing rule JSON files
        
    Returns:
        Dictionary with discovered patterns:
        - exact_subtrees: Counter of exact pattern hashes
        - abstract_algorithms: Counter of normalized pattern hashes
        - hash_to_tree: Dict mapping hash -> actual subtree tuple
        - subtree_metadata: Dict mapping hash -> {count, fitness_sum, files}
        - common_functions: Counter (backward compatibility)
        - common_thresholds: Counter (backward compatibility)
        - common_structures: Counter (backward compatibility)
    """
    patterns = {
        "exact_subtrees": Counter(),
        "abstract_algorithms": Counter(),
        "hash_to_tree": {},
        "subtree_metadata": {},
        "common_thresholds": Counter(),
        "common_functions": Counter(),
        "common_combinations": Counter(),
        "common_structures": Counter(),
    }
    
    # Extract known alert messages from terminals
    alert_messages = {
        term for term in TERMINALS 
        if isinstance(term, str) and len(term) > 5
    }
    
    # Only process champion files, not checkpoint files
    rule_files = [f for f in rules_dir.glob("*.json") 
                  if "champion" in f.name and "checkpoint" not in f.name]

    for rule_file in rule_files:
        try:
            rule_data = load_rule(rule_file)
            tree = normalize_tree_structure(rule_data["tree"])
            fitness = rule_data.get("fitness", 0.0)
            tree_str = str(tree)
            
            # Get all sub-components of this tree
            all_subtrees = extract_subtrees(tree, min_nodes=2)
            
            for subtree in all_subtrees:
                # 1. Exact Hash (specific implementation)
                exact_h = merkle_hash(subtree, normalize_vars=False, 
                                     alert_messages=alert_messages)
                patterns["exact_subtrees"][exact_h] += 1
                
                # Store the actual code for reconstruction
                if exact_h not in patterns["hash_to_tree"]:
                    patterns["hash_to_tree"][exact_h] = subtree
                
                # Track metadata
                if exact_h not in patterns["subtree_metadata"]:
                    patterns["subtree_metadata"][exact_h] = {
                        "count": 0,
                        "fitness_sum": 0.0,
                        "files": []
                    }
                patterns["subtree_metadata"][exact_h]["count"] += 1
                patterns["subtree_metadata"][exact_h]["fitness_sum"] += fitness
                patterns["subtree_metadata"][exact_h]["files"].append(rule_file.name)
                
                # 2. Abstract Hash (algorithm pattern)
                if isinstance(subtree, tuple):
                    abstract_h = merkle_hash(subtree, normalize_vars=True,
                                            alert_messages=alert_messages)
                    patterns["abstract_algorithms"][abstract_h] += 1
            
            # Maintain backward compatibility: still track simple patterns
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
            
            # Find common combinations (backward compatibility)
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


def discover_common_patterns(rules_dir: Path) -> Dict[str, Any]:
    """
    Discover common patterns in evolved rules.
    
    This function maintains backward compatibility by calling discover_structural_patterns()
    and mapping the results to the old format.
    
    Args:
        rules_dir: Directory containing rule JSON files
        
    Returns:
        Dictionary with discovered patterns (backward compatible format)
    """
    # Use new structural discovery
    structural_patterns = discover_structural_patterns(rules_dir)
    
    # Return in old format for backward compatibility
    return {
        "common_thresholds": structural_patterns.get("common_thresholds", Counter()),
        "common_functions": structural_patterns.get("common_functions", Counter()),
        "common_combinations": structural_patterns.get("common_combinations", Counter()),
        "common_structures": structural_patterns.get("common_structures", Counter()),
        # Also include new fields for code that wants to use them
        "exact_subtrees": structural_patterns.get("exact_subtrees", Counter()),
        "abstract_algorithms": structural_patterns.get("abstract_algorithms", Counter()),
        "hash_to_tree": structural_patterns.get("hash_to_tree", {}),
        "subtree_metadata": structural_patterns.get("subtree_metadata", {}),
    }


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

