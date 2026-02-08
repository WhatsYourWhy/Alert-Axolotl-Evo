"""Tests for genetic operators."""

import pytest

from alert_axolotl_evo.operators import (
    initialize_population,
    point_mutation,
    subtree_crossover,
    tournament_select,
)


def test_initialize_population():
    """Test population initialization."""
    pop = initialize_population(pop_size=10, min_depth=2, max_depth=5)
    assert len(pop) == 10
    assert all(isinstance(tree, (tuple, str, int)) for tree in pop)


def test_tournament_select():
    """Test tournament selection."""
    scored = [
        (("if_alert", (">", "latency", 100), "alert"), 8.5),
        (("if_alert", (">", "latency", 50), "alert"), 7.0),
        (("if_alert", (">", "latency", 200), "alert"), 6.0),
        (("if_alert", (">", "latency", 150), "alert"), 5.0),
    ]
    
    selected = tournament_select(scored, size=2)
    assert selected in [tree for tree, _ in scored]


def test_subtree_crossover():
    """Test subtree crossover."""
    parent_a = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    parent_b = ("if_alert", ("<", ("avg", "latency"), 50), "Low alert!")
    
    child_a, child_b = subtree_crossover(parent_a, parent_b)
    
    assert child_a is not None
    assert child_b is not None
    # Children should be different from parents (usually)
    assert child_a != parent_a or child_b != parent_b


def test_point_mutation():
    """Test point mutation."""
    tree = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    mutated = point_mutation(tree, max_depth=3)
    
    assert mutated is not None
    # Mutation should change the tree (usually)
    assert isinstance(mutated, (tuple, str, int))

