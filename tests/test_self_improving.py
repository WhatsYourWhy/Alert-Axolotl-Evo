"""Tests for self-improving module."""

import tempfile
from pathlib import Path

import pytest

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.self_improving import SelfImprovingEvolver
from alert_axolotl_evo.persistence import save_rule
from alert_axolotl_evo.primitives import FUNCTIONS, TERMINALS


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


def test_auto_register_primitives():
    """Test automatic primitive registration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            auto_register=True,
            min_pattern_usage=3
        )
        
        # Create multiple rule files with "avg+>" pattern to trigger registration
        for i in range(5):
            rule_file = evolver.results_dir / f"run_{i}_champion.json"
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                fitness=8.0 + i,
                generation=10,
                output_path=rule_file,
            )
        
        # Check that avg_gt is not yet registered
        assert "avg_gt" not in FUNCTIONS
        
        # Auto-register primitives
        registered = evolver.auto_register_primitives()
        
        # Verify primitives were registered
        assert len(registered) > 0
        assert "avg_gt" in registered
        assert "avg_gt" in FUNCTIONS
        
        # Verify no duplicate registrations
        registered_again = evolver.auto_register_primitives()
        assert len(registered_again) == 0  # Should not register again


def test_auto_register_thresholds():
    """Test automatic threshold terminal registration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            auto_register=True,
            min_pattern_usage=2
        )
        
        # Create multiple rules with the same threshold value to meet min_pattern_usage
        threshold = 125  # Value not in default TERMINALS
        for i in range(3):  # Create 3 rules with same threshold
            rule_file = evolver.results_dir / f"run_{i}_champion.json"
            save_rule(
                ("if_alert", (">", ("avg", "latency"), threshold), "alert"),
                fitness=8.0,
                generation=10,
                output_path=rule_file,
            )
        
        # Auto-register primitives
        registered = evolver.auto_register_primitives()
        
        # Verify threshold was registered (should appear 3 times, >= min_pattern_usage of 2)
        threshold_registered = [r for r in registered if r.startswith("threshold_")]
        assert len(threshold_registered) > 0, f"Expected threshold registration, got: {registered}"
        
        # Verify threshold is in TERMINALS
        assert threshold in TERMINALS, f"Threshold {threshold} should be in TERMINALS"


def test_adapt_data_generation():
    """Test adaptive data generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            adapt_data=True
        )
        
        # Create history with low complexity to trigger adaptation
        evolver.history = [
            {
                "run_id": "run_0",
                "config": Config().to_dict(),
                "fitness": 2.0,
                "generation": 5,
                "rule_complexity": 3,  # Low complexity
                "rule_hash": "abc123",
            },
            {
                "run_id": "run_1",
                "config": Config().to_dict(),
                "fitness": 2.1,
                "generation": 5,
                "rule_complexity": 4,  # Low complexity
                "rule_hash": "def456",
            },
        ]
        
        # Create some rule files for pattern discovery
        for i in range(2):
            rule_file = evolver.results_dir / f"run_{i}_champion.json"
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                fitness=2.0 + i * 0.1,
                generation=5,
                output_path=rule_file,
            )
        
        config = Config()
        original_size = config.data.mock_size
        original_multiplier = config.data.anomaly_multiplier
        
        # Adapt data generation
        adapted_config = evolver.adapt_data_generation(config)
        
        # Verify mock data was adapted (low complexity should increase mock_size)
        assert adapted_config.data.mock_size >= original_size
        
        # Verify original config was not mutated
        assert config.data.mock_size == original_size
        
        # Verify adaptations are tracked
        assert len(evolver.data_adaptations) > 0
        
        # Test that real data configs are NOT modified
        csv_config = Config()
        csv_config.data.data_source = "csv"
        csv_config.data.data_path = Path("test.csv")
        adapted_csv = evolver.adapt_data_generation(csv_config)
        assert adapted_csv.data.data_source == "csv"
        assert adapted_csv.data.data_path == csv_config.data.data_path


def test_feature_flags():
    """Test feature flags for enabling/disabling features."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test auto_register=False
        evolver_no_auto = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            auto_register=False
        )
        assert evolver_no_auto.auto_register is False
        
        # Test adapt_data=False
        evolver_no_adapt = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            adapt_data=False
        )
        assert evolver_no_adapt.adapt_data is False
        
        # Test min_pattern_usage
        evolver_custom = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            min_pattern_usage=10
        )
        assert evolver_custom.min_pattern_usage == 10
        
        # Test both disabled
        evolver_both_off = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            auto_register=False,
            adapt_data=False
        )
        assert evolver_both_off.auto_register is False
        assert evolver_both_off.adapt_data is False


def test_init_with_new_parameters():
    """Test initialization with new parameters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            auto_register=True,
            adapt_data=True,
            min_pattern_usage=5
        )
        
        # Verify all parameters are set
        assert evolver.auto_register is True
        assert evolver.adapt_data is True
        assert evolver.min_pattern_usage == 5
        
        # Verify tracking lists are initialized empty
        assert len(evolver.registered_primitives) == 0
        assert len(evolver.data_adaptations) == 0
        
        # Test default values
        evolver_default = SelfImprovingEvolver(results_dir=Path(tmpdir))
        assert evolver_default.auto_register is True  # Default
        assert evolver_default.adapt_data is True  # Default
        assert evolver_default.min_pattern_usage == 5  # Default


def test_performance_report_new_fields():
    """Test performance report includes new fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Create some history
        evolver.history = [
            {
                "run_id": "run_0",
                "config": Config().to_dict(),
                "fitness": 8.0,
                "generation": 10,
                "rule_complexity": 5,
                "rule_hash": "abc123",
            }
        ]
        
        # Add some registered primitives
        evolver.registered_primitives = ["avg_gt", "threshold_125"]
        
        # Add some data adaptations
        evolver.data_adaptations = [
            {
                "run_id": 1,
                "changes": {
                    "mock_size": {
                        "old": 100,
                        "new": 115,
                        "reason": "Low rule complexity"
                    }
                }
            }
        ]
        
        # Create sample rules for report
        for i in range(2):
            rule_file = evolver.results_dir / f"run_{i}_champion.json"
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                fitness=8.0,
                generation=10,
                output_path=rule_file,
            )
        
        # Generate report
        report = evolver.get_performance_report()
        
        # Verify new fields exist
        assert "auto_registered_primitives" in report
        assert "data_adaptations" in report
        
        # Verify fields contain data
        assert isinstance(report["auto_registered_primitives"], list)
        assert len(report["auto_registered_primitives"]) > 0
        assert isinstance(report["data_adaptations"], list)
        assert len(report["data_adaptations"]) > 0

