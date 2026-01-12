"""Genetic operators: crossover, mutation, selection, and initialization."""

import random
from typing import Any, List, Optional, Tuple

from alert_axolotl_evo.primitives import ARITIES, BOOLEAN_FUNCTIONS, FUNCTION_NAMES, MSG_TERMINALS, TERMINALS
from alert_axolotl_evo.tree import ensure_alert_root, get_subtree_paths, is_valid_subtree, node_count, replace_subtree


def random_terminal(rng: Optional[random.Random] = None) -> Any:
    """Select a random terminal."""
    if rng is None:
        rng = random
    return rng.choice(TERMINALS)


def random_numeric_terminal(rng: Optional[random.Random] = None) -> Any:
    """
    Select a random numeric terminal (for condition generation).
    
    Only returns numeric values (int/float) or variable names (like "latency").
    Explicitly excludes message terminals to prevent contamination of condition space.
    """
    if rng is None:
        rng = random
    # Only numeric values and variable names (like "latency")
    # Explicitly exclude all message strings
    numeric_terminals = [
        t for t in TERMINALS 
        if isinstance(t, (int, float)) or 
        (isinstance(t, str) and t not in MSG_TERMINALS and t == "latency")  # Only allow "latency" variable
    ]
    # Fallback to "latency" if no numeric terminals found (shouldn't happen)
    return rng.choice(numeric_terminals) if numeric_terminals else "latency"


def random_boolean_function(rng: Optional[random.Random] = None) -> str:
    """Select a random boolean-returning function."""
    if rng is None:
        rng = random
    return rng.choice(BOOLEAN_FUNCTIONS)


def random_function(rng: Optional[random.Random] = None) -> str:
    """Select a random function."""
    if rng is None:
        rng = random
    return rng.choice(FUNCTION_NAMES)


def grow_condition_subtree(depth: int, max_depth: int, rng: Optional[random.Random] = None) -> Any:
    """
    Grow method for condition subtrees.
    
    Conditions can contain:
    - Boolean functions (>, <, >=, <=, and, or, not) at any level
    - Statistical functions (avg, max, min, etc.) that return numeric values
    - Numeric terminals and variable references
    
    At root level, prefers boolean functions (comparisons).
    Statistical functions are used to compute values for comparison.
    """
    if rng is None:
        rng = random
    
    if depth >= max_depth or (depth > 0 and rng.random() < 0.5):
        # At leaf, prefer terminals or simple statistical functions
        if rng.random() < 0.4 and depth < max_depth:
            # Use avg("latency") for computing values
            return ("avg", "latency")
        return random_numeric_terminal(rng) if rng.random() < 0.5 else "latency"
    
    # At root or higher levels, prefer boolean functions for structure
    if depth == 0 or rng.random() < 0.7:
        # Boolean function (comparison or logical)
        func = random_boolean_function(rng)
        if func == "not":
            return (func, grow_condition_subtree(depth + 1, max_depth, rng))
        return (func, grow_condition_subtree(depth + 1, max_depth, rng), grow_condition_subtree(depth + 1, max_depth, rng))
    else:
        # Statistical function (returns numeric value for comparison)
        func = rng.choice(["avg", "max", "min"])
        # Statistical functions need a list - use "latency" variable
        return (func, "latency")


def full_condition_subtree(depth: int, max_depth: int, rng: Optional[random.Random] = None) -> Any:
    """
    Full method for condition subtrees.
    
    Conditions can contain boolean and statistical functions.
    """
    if rng is None:
        rng = random
    
    if depth >= max_depth:
        return random_numeric_terminal(rng) if rng.random() < 0.5 else "latency"
    
    # At root or higher levels, prefer boolean functions
    if depth == 0 or rng.random() < 0.7:
        # Boolean function
        func = random_boolean_function(rng)
        if func == "not":
            return (func, full_condition_subtree(depth + 1, max_depth, rng))
        return (func, full_condition_subtree(depth + 1, max_depth, rng), full_condition_subtree(depth + 1, max_depth, rng))
    else:
        # Statistical function (returns numeric value)
        func = rng.choice(["avg", "max", "min"])
        return (func, "latency")


def make_alert_tree(depth: int, max_depth: int, use_full: bool = False, rng: Optional[random.Random] = None) -> Any:
    """
    Create a valid alert rule tree with if_alert at root.
    
    Always returns: ("if_alert", <condition_subtree>, <message_terminal>)
    
    Args:
        depth: Current depth (should be 0 for root)
        max_depth: Maximum depth for condition subtree
        use_full: If True, use full method; otherwise use grow method
        rng: Optional random number generator (for determinism)
        
    Returns:
        Valid alert rule tree with if_alert at root
    """
    if rng is None:
        rng = random
    
    if use_full:
        condition = full_condition_subtree(0, max_depth, rng)
    else:
        condition = grow_condition_subtree(0, max_depth, rng)
    message = rng.choice(MSG_TERMINALS)
    return ("if_alert", condition, message)


def grow_tree(depth: int, max_depth: int) -> Any:
    """Grow method: choose function or terminal stochastically."""
    if depth == 0 and random.random() < 0.4:
        avg_subtree = ("avg", grow_tree(depth + 1, max_depth))
        if random.random() < 0.5:
            return avg_subtree
        return ("if_alert", avg_subtree, random_terminal())
    if depth >= max_depth or (depth > 0 and random.random() < 0.5):
        return random_terminal()
    func = random_function()
    if func == "avg":
        return (func, grow_tree(depth + 1, max_depth))
    if func == "if_alert":
        return (func, grow_tree(depth + 1, max_depth), random_terminal())
    return (func, grow_tree(depth + 1, max_depth), grow_tree(depth + 1, max_depth))


def full_tree(depth: int, max_depth: int) -> Any:
    """Full method: always expand until max_depth."""
    if depth == 0 and random.random() < 0.4:
        avg_subtree = ("avg", full_tree(depth + 1, max_depth))
        if random.random() < 0.5:
            return avg_subtree
        return ("if_alert", avg_subtree, random_terminal())
    if depth >= max_depth:
        return random_terminal()
    func = random_function()
    if func == "avg":
        return (func, full_tree(depth + 1, max_depth))
    if func == "if_alert":
        return (func, full_tree(depth + 1, max_depth), random_terminal())
    return (func, full_tree(depth + 1, max_depth), full_tree(depth + 1, max_depth))


def initialize_population(pop_size: int, min_depth: int, max_depth: int, rng: Optional[random.Random] = None) -> List[Any]:
    """
    Koza ramped half-and-half initialization.
    
    All trees are guaranteed to have if_alert at root (valid alert rules).
    
    Args:
        pop_size: Size of population to generate
        min_depth: Minimum tree depth
        max_depth: Maximum tree depth
        rng: Optional random number generator (for determinism)
    """
    if rng is None:
        rng = random
    
    population: List[Any] = []
    depths = list(range(min_depth, max_depth + 1))
    while len(population) < pop_size:
        for depth in depths:
            if len(population) >= pop_size:
                break
            if len(population) % 2 == 0:
                # Use grow method
                population.append(make_alert_tree(0, depth, use_full=False, rng=rng))
            else:
                # Use full method
                population.append(make_alert_tree(0, depth, use_full=True, rng=rng))
    return population


def tournament_select(scored: List[Tuple[Any, float]], size: int = 4) -> Any:
    """Tournament selection."""
    contenders = random.sample(scored, size)
    contenders.sort(key=lambda item: (-item[1], node_count(item[0])))
    return contenders[0][0]


def subtree_crossover(parent_a: Any, parent_b: Any) -> Tuple[Any, Any]:
    """
    Swap random subtrees between two parents.
    
    Never swaps root node (path ()) to preserve if_alert requirement.
    """
    paths_a = [(path, subtree) for path, subtree in get_subtree_paths(parent_a) 
                if path != () and is_valid_subtree(subtree, ARITIES)]
    paths_b = [(path, subtree) for path, subtree in get_subtree_paths(parent_b) 
                if path != () and is_valid_subtree(subtree, ARITIES)]
    if not paths_a or not paths_b:
        return parent_a, parent_b
    path_a, subtree_a = random.choice(paths_a)
    path_b, subtree_b = random.choice(paths_b)
    child_a = replace_subtree(parent_a, path_a, subtree_b)
    child_b = replace_subtree(parent_b, path_b, subtree_a)
    if not is_valid_subtree(child_a, ARITIES) or not is_valid_subtree(child_b, ARITIES):
        return parent_a, parent_b
    # Repair to ensure if_alert at root (defense in depth)
    child_a = ensure_alert_root(child_a)
    child_b = ensure_alert_root(child_b)
    return child_a, child_b


def point_mutation(tree: Any, max_depth: int = 2) -> Any:
    """
    Replace a random subtree with a new random grow tree.
    
    Never mutates root node (path ()) to preserve if_alert requirement.
    """
    paths = get_subtree_paths(tree)
    # Filter out root path
    non_root_paths = [(path, subtree) for path, subtree in paths if path != ()]
    if not non_root_paths:
        return tree
    path, _ = random.choice(non_root_paths)
    new_subtree = grow_condition_subtree(0, max_depth)
    result = replace_subtree(tree, path, new_subtree)
    # Repair to ensure if_alert at root (defense in depth)
    return ensure_alert_root(result)

