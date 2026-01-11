"""Tests for tree utilities."""

import pytest

from alert_axolotl_evo.tree import (
    get_subtree_paths,
    is_valid_subtree,
    node_count,
    replace_subtree,
    tree_hash,
)


def test_tree_hash():
    """Test tree hashing."""
    tree1 = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    tree2 = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    tree3 = ("if_alert", (">", ("avg", "latency"), 200), "High alert!")
    
    assert tree_hash(tree1) == tree_hash(tree2)
    assert tree_hash(tree1) != tree_hash(tree3)
    assert len(tree_hash(tree1)) == 6


def test_node_count():
    """Test node counting."""
    tree1 = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    assert node_count(tree1) == 6  # if_alert, >, avg, latency, 100, "High alert!"
    
    tree2 = "latency"
    assert node_count(tree2) == 1
    
    tree3 = ("avg", "latency")
    assert node_count(tree3) == 2


def test_get_subtree_paths():
    """Test subtree path collection."""
    tree = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    paths = get_subtree_paths(tree)
    
    assert len(paths) > 0
    assert ((), tree) in paths
    assert any(path == (1,) for path, _ in paths)


def test_replace_subtree():
    """Test subtree replacement."""
    tree = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    new_subtree = ("<", "latency", 50)
    
    result = replace_subtree(tree, (1,), new_subtree)
    assert result[1] == new_subtree
    assert result[0] == "if_alert"
    assert result[2] == "High alert!"


def test_is_valid_subtree():
    """Test subtree validation."""
    from alert_axolotl_evo.primitives import ARITIES
    
    valid_tree = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    assert is_valid_subtree(valid_tree, ARITIES) is True
    
    invalid_tree = ("if_alert", (">", ("avg", "latency")))  # Missing argument
    assert is_valid_subtree(invalid_tree, ARITIES) is False
    
    terminal = "latency"
    assert is_valid_subtree(terminal, ARITIES) is True

