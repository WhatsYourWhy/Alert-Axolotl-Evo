"""Tests for self-improving module."""

import tempfile
from pathlib import Path

import pytest

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.persistence import save_rule


def test_self_improving_evolver_init():
    """Test self-improving evolver initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        assert evolver.results_dir.exists()
        assert len(evolver.history) == 0
        assert evolver.learned_config is None


def test_get_optimal_config():
    """Test getting optimal config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Without history, should return base config
        base_config = Config()
        optimal = evolver.get_optimal_config(base_config)
        assert optimal.evolution.pop_size == base_config.evolution.pop_size


def test_suggest_improvements():
    """Test improvement suggestions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Create some sample rule files
        for i in range(3):
            rule_file = evolver.results_dir / f"rule_{i}.json"
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                fitness=8.0 + i,
                generation=10,
                output_path=rule_file,
            )
        
        suggestions = evolver.suggest_improvements()
        assert isinstance(suggestions, list)


def test_get_performance_report():
    """Test performance report generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Create sample rules
        for i in range(2):
            rule_file = evolver.results_dir / f"rule_{i}.json"
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                fitness=8.0,
                generation=10,
                output_path=rule_file,
            )
        
        report = evolver.get_performance_report()
        assert "metrics" in report or "error" in report

