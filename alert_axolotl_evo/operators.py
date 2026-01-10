"""Genetic operators: crossover, mutation, selection, and initialization."""

import random
from typing import Any, List, Tuple

from alert_axolotl_evo.primitives import ARITIES, FUNCTION_NAMES, TERMINALS
from alert_axolotl_evo.tree import get_subtree_paths, is_valid_subtree, node_count, replace_subtree


def random_terminal() -> Any:
    """Select a random terminal."""
    return random.choice(TERMINALS)


def random_function() -> str:
    """Select a random function."""
    return random.choice(FUNCTION_NAMES)


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


def initialize_population(pop_size: int, min_depth: int, max_depth: int) -> List[Any]:
    """Koza ramped half-and-half initialization."""
    population: List[Any] = []
    depths = list(range(min_depth, max_depth + 1))
    while len(population) < pop_size:
        for depth in depths:
            if len(population) >= pop_size:
                break
            if len(population) % 2 == 0:
                population.append(grow_tree(0, depth))
            else:
                population.append(full_tree(0, depth))
    return population


def tournament_select(scored: List[Tuple[Any, float]], size: int = 4) -> Any:
    """Tournament selection."""
    contenders = random.sample(scored, size)
    contenders.sort(key=lambda item: (-item[1], node_count(item[0])))
    return contenders[0][0]


def subtree_crossover(parent_a: Any, parent_b: Any) -> Tuple[Any, Any]:
    """Swap random subtrees between two parents."""
    paths_a = [(path, subtree) for path, subtree in get_subtree_paths(parent_a) if is_valid_subtree(subtree, ARITIES)]
    paths_b = [(path, subtree) for path, subtree in get_subtree_paths(parent_b) if is_valid_subtree(subtree, ARITIES)]
    if not paths_a or not paths_b:
        return parent_a, parent_b
    path_a, subtree_a = random.choice(paths_a)
    path_b, subtree_b = random.choice(paths_b)
    child_a = replace_subtree(parent_a, path_a, subtree_b)
    child_b = replace_subtree(parent_b, path_b, subtree_a)
    if not is_valid_subtree(child_a, ARITIES) or not is_valid_subtree(child_b, ARITIES):
        return parent_a, parent_b
    return child_a, child_b


def point_mutation(tree: Any, max_depth: int = 2) -> Any:
    """Replace a random subtree with a new random grow tree."""
    paths = get_subtree_paths(tree)
    path, _ = random.choice(paths)
    new_subtree = grow_tree(0, max_depth)
    return replace_subtree(tree, path, new_subtree)

