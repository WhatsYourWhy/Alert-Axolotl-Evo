"""Tests for analytics module."""

import tempfile
from pathlib import Path

import pytest

from alert_axolotl_evo.analytics import (
    analyze_evolution_results,
    calculate_convergence_rate,
    identify_successful_configs,
    track_performance_metrics,
)
from alert_axolotl_evo.persistence import save_checkpoint, save_rule


def test_analyze_evolution_results():
    """Test evolution results analysis."""
    with tempfile.TemporaryDirectory() as tmpdir:
        results_dir = Path(tmpdir)
        
        # Create sample rule file
        rule_file = results_dir / "test_champion.json"
        save_rule(
            ("if_alert", (">", ("avg", "latency"), 100), "alert"),
            fitness=8.5,
            generation=10,
            output_path=rule_file,
        )
        
        # Analyze
        results = analyze_evolution_results(results_dir)
        assert len(results) >= 1
        assert any(r.get("fitness") == 8.5 for r in results)


def test_track_performance_metrics():
    """Test performance metrics tracking."""
    results = [
        {"fitness": 8.5, "generation": 10, "complexity": 5},
        {"fitness": 7.2, "generation": 15, "complexity": 6},
        {"fitness": 9.1, "generation": 20, "complexity": 4},
    ]
    
    metrics = track_performance_metrics(results)
    assert metrics["total_runs"] == 3
    assert metrics["avg_fitness"] == pytest.approx(8.27, abs=0.1)
    assert metrics["max_fitness"] == 9.1
    assert metrics["min_fitness"] == 7.2


def test_identify_successful_configs():
    """Test successful config identification."""
    results = [
        {"config": {"evolution": {"pop_size": 50}, "operators": {"mutation_rate": 0.2}}, "fitness": 8.5},
        {"config": {"evolution": {"pop_size": 30}, "operators": {"mutation_rate": 0.1}}, "fitness": 7.2},
        {"config": {"evolution": {"pop_size": 100}, "operators": {"mutation_rate": 0.3}}, "fitness": 9.1},
    ]
    
    successful = identify_successful_configs(results, top_n=2)
    assert len(successful) == 2
    assert successful[0]["fitness"] == 9.1  # Best first
    assert successful[1]["fitness"] == 8.5


def test_calculate_convergence_rate():
    """Test convergence rate calculation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_file = Path(tmpdir) / "checkpoint.json"
        save_checkpoint(
            population=[],
            generation=5,
            seed=42,
            champion=("test",),
            champion_fitness=8.5,
            champion_history=[(("tree1",), 5.0), (("tree2",), 7.0), (("tree3",), 8.5)],
            output_path=checkpoint_file,
        )
        
        rate = calculate_convergence_rate(checkpoint_file)
        assert rate is not None
        assert rate > 0

