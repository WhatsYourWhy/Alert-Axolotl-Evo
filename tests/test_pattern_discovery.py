"""Tests for pattern discovery with Merkle hashing."""

import tempfile
from pathlib import Path

import pytest

from alert_axolotl_evo.pattern_discovery import (
    discover_structural_patterns,
    extract_subtrees,
)
from alert_axolotl_evo.persistence import save_rule
from alert_axolotl_evo.tree import merkle_hash, normalize_tree_structure
from alert_axolotl_evo.visualization import generate_pattern_name


def test_merkle_hash_exact_consistency():
    """Same tree = same hash."""
    tree1 = (">", ("avg", "latency"), 100)
    tree2 = (">", ("avg", "latency"), 100)
    assert merkle_hash(tree1) == merkle_hash(tree2)


def test_merkle_hash_different_vars():
    """Different variables = different exact hash."""
    tree1 = (">", ("avg", "latency"), 100)
    tree2 = (">", ("avg", "cpu"), 100)
    assert merkle_hash(tree1) != merkle_hash(tree2)


def test_merkle_hash_abstract_normalization():
    """Same structure, different vars = same abstract hash."""
    tree1 = (">", ("avg", "latency"), 100)
    tree2 = (">", ("avg", "cpu"), 100)
    hash1 = merkle_hash(tree1, normalize_vars=True)
    hash2 = merkle_hash(tree2, normalize_vars=True)
    assert hash1 == hash2


def test_merkle_hash_abstract_different_structure():
    """Different structure = different abstract hash."""
    tree1 = (">", ("avg", "latency"), 100)
    tree2 = ("<", ("max", "latency"), 100)
    hash1 = merkle_hash(tree1, normalize_vars=True)
    hash2 = merkle_hash(tree2, normalize_vars=True)
    assert hash1 != hash2


def test_merkle_hash_alert_messages_not_normalized():
    """Alert messages should not be normalized."""
    tree1 = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    tree2 = ("if_alert", (">", ("avg", "cpu"), 100), "High alert!")
    # Exact hashes should differ (different vars)
    assert merkle_hash(tree1) != merkle_hash(tree2)
    # Abstract hashes should be same (same structure, alert preserved)
    alert_messages = {"High alert!"}
    hash1 = merkle_hash(tree1, normalize_vars=True, alert_messages=alert_messages)
    hash2 = merkle_hash(tree2, normalize_vars=True, alert_messages=alert_messages)
    assert hash1 == hash2


def test_merkle_hash_numeric_constants_preserved():
    """Numeric constants should be preserved (not normalized)."""
    tree1 = (">", ("avg", "latency"), 100)
    tree2 = (">", ("avg", "latency"), 150)
    # Different thresholds = different hashes even with normalization
    hash1 = merkle_hash(tree1, normalize_vars=True)
    hash2 = merkle_hash(tree2, normalize_vars=True)
    assert hash1 != hash2


def test_list_tuple_equivalence():
    """Lists and tuples should hash the same."""
    tree_list = [">", ["avg", "latency"], 100]
    tree_tuple = (">", ("avg", "latency"), 100)
    assert merkle_hash(tree_list) == merkle_hash(tree_tuple)


def test_nested_structure():
    """Nested structures hash correctly."""
    tree = ("and", 
            (">", ("avg", "latency"), 100),
            ("<", ("max", "latency"), 200))
    hash_val = merkle_hash(tree)
    # Should be deterministic
    assert hash_val == merkle_hash(tree)


def test_normalize_tree_structure():
    """Normalize converts lists to tuples."""
    tree_list = [">", ["avg", "latency"], 100]
    normalized = normalize_tree_structure(tree_list)
    assert isinstance(normalized, tuple)
    assert normalized == (">", ("avg", "latency"), 100)


def test_extract_subtrees():
    """Correctly extracts all subtrees."""
    tree = ("and",
            (">", ("avg", "latency"), 100),
            ("<", ("max", "latency"), 200))
    
    subtrees = extract_subtrees(tree, min_nodes=2)
    
    # Should include the full tree and all non-trivial subtrees
    assert len(subtrees) >= 3  # Full tree + at least 2 comparison subtrees
    assert tree in subtrees or normalize_tree_structure(tree) in subtrees


def test_extract_subtrees_min_nodes():
    """Respects min_nodes filter."""
    tree = (">", ("avg", "latency"), 100)
    
    subtrees_min2 = extract_subtrees(tree, min_nodes=2)
    subtrees_min5 = extract_subtrees(tree, min_nodes=5)
    
    # Tree has 3 nodes, so should appear in min_nodes=2 but not min_nodes=5
    assert len(subtrees_min2) >= 1
    assert len(subtrees_min5) == 0


def test_discover_structural_patterns():
    """Finds exact and abstract patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        
        # Create rules with known patterns
        for i in range(3):
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "High alert!"),
                fitness=8.0 + i * 0.1,
                generation=10,
                output_path=results_dir / f"rule_{i}_champion.json",
            )
        
        patterns = discover_structural_patterns(results_dir)
        
        # Should find exact patterns
        assert "exact_subtrees" in patterns
        assert len(patterns["exact_subtrees"]) > 0
        
        # Should find abstract algorithms
        assert "abstract_algorithms" in patterns
        assert len(patterns["abstract_algorithms"]) > 0
        
        # Should have hash_to_tree mapping
        assert "hash_to_tree" in patterns
        assert len(patterns["hash_to_tree"]) > 0
        
        # Should have metadata
        assert "subtree_metadata" in patterns
        assert len(patterns["subtree_metadata"]) > 0


def test_pattern_naming_deterministic():
    """Same pattern = same name."""
    subtree1 = (">", ("avg", "latency"), 100)
    subtree2 = (">", ("avg", "latency"), 100)
    
    hash1 = merkle_hash(subtree1)
    hash2 = merkle_hash(subtree2)
    
    name1 = generate_pattern_name(hash1, subtree1)
    name2 = generate_pattern_name(hash2, subtree2)
    
    assert name1 == name2


def test_pattern_discovery_integration():
    """End-to-end test with real rule files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from alert_axolotl_evo.self_improving import SelfImprovingEvolver
        
        evolver = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            auto_register=True,
            min_pattern_usage=2
        )
        
        # Create rules with patterns
        for i in range(3):
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "High alert!"),
                fitness=8.0,
                generation=10,
                output_path=evolver.results_dir / f"run_{i}_champion.json",
            )
        
        # Should discover patterns
        patterns = discover_structural_patterns(evolver.results_dir)
        assert len(patterns["exact_subtrees"]) > 0
