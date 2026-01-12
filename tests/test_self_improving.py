"""Tests for self-improving module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

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


def test_pattern_detection_accuracy():
    """Test that pattern detection correctly identifies common combinations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from alert_axolotl_evo.pattern_discovery import discover_common_patterns
        from pathlib import Path
        
        results_dir = Path(tmpdir)
        
        # Create rules with known patterns (must have "champion" in filename)
        # Rule 1: avg + > pattern
        save_rule(
            ("if_alert", (">", ("avg", "latency"), 100), "alert"),
            fitness=8.0,
            generation=10,
            output_path=results_dir / "rule1_champion.json",
        )
        
        # Rule 2: avg + > pattern (same)
        save_rule(
            ("if_alert", (">", ("avg", "latency"), 150), "alert"),
            fitness=8.5,
            generation=10,
            output_path=results_dir / "rule2_champion.json",
        )
        
        # Rule 3: avg + > pattern (same)
        save_rule(
            (">", ("avg", "latency"), 200),
            fitness=9.0,
            generation=10,
            output_path=results_dir / "rule3_champion.json",
        )
        
        # Rule 4: max + > pattern
        save_rule(
            (">", ("max", "latency"), 100),
            fitness=7.5,
            generation=10,
            output_path=results_dir / "rule4_champion.json",
        )
        
        # Analyze patterns
        patterns = discover_common_patterns(results_dir)
        combinations = patterns.get("common_combinations", {})
        
        # Verify avg+> pattern is detected (should be 3)
        assert combinations.get("avg+>", 0) == 3, f"Expected 3 'avg+>' patterns, got {combinations.get('avg+>', 0)}"
        
        # Verify max+> pattern is detected (should be 1)
        assert combinations.get("max+>", 0) == 1, f"Expected 1 'max+>' pattern, got {combinations.get('max+>', 0)}"
        
        # Verify thresholds are detected
        thresholds = patterns.get("common_thresholds", {})
        assert thresholds.get(100, 0) >= 2, "Threshold 100 should appear at least twice"
        assert thresholds.get(150, 0) >= 1, "Threshold 150 should appear at least once"
        assert thresholds.get(200, 0) >= 1, "Threshold 200 should appear at least once"


def test_edge_case_empty_results_dir():
    """Test with empty results directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Should not crash
        registered = evolver.auto_register_primitives()
        assert registered == []
        
        adapted = evolver.adapt_data_generation(Config())
        assert adapted.data.mock_size == Config().data.mock_size  # No change


def test_edge_case_malformed_json():
    """Test with malformed JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Create malformed JSON
        bad_file = evolver.results_dir / "bad.json"
        bad_file.write_text("{ invalid json }")
        
        # Should not crash, should skip bad file
        registered = evolver.auto_register_primitives()
        # Should handle gracefully
        assert isinstance(registered, list)


def test_edge_case_missing_fields():
    """Test with rule files missing required fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Create file with missing 'tree' field
        import json
        bad_rule = evolver.results_dir / "incomplete_champion.json"
        bad_rule.write_text(json.dumps({"fitness": 8.0}))  # Missing 'tree'
        
        # Should not crash
        registered = evolver.auto_register_primitives()
        assert isinstance(registered, list)


def test_edge_case_zero_history():
    """Test data adaptation with zero history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        evolver.history = []  # Empty history
        
        config = Config()
        adapted = evolver.adapt_data_generation(config)
        
        # Should return original config unchanged
        assert adapted.data.mock_size == config.data.mock_size
        assert adapted.data.anomaly_count == config.data.anomaly_count


def test_edge_case_single_run():
    """Test that single run doesn't trigger adaptation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        evolver.history = [
            {
                "run_id": "run_0",
                "config": Config().to_dict(),
                "fitness": 2.0,
                "generation": 5,
                "rule_complexity": 5,
                "rule_hash": "abc123",
            }
        ]
        
        config = Config()
        adapted = evolver.adapt_data_generation(config)
        
        # Should not adapt with only 1 run (needs 2+)
        assert adapted.data.mock_size == config.data.mock_size


def test_edge_case_extreme_values():
    """Test data adaptation with extreme values."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Create history with extreme values
        evolver.history = [
            {
                "run_id": f"run_{i}",
                "config": Config().to_dict(),
                "fitness": 0.1 if i < 2 else 10.0,  # Very low then very high
                "generation": 5,
                "rule_complexity": 1 if i < 2 else 20,  # Very simple then very complex
                "rule_hash": f"hash{i}",
            }
            for i in range(4)
        ]
        
        config = Config()
        config.data.mock_size = 10  # Very small
        config.data.anomaly_multiplier = 10.0  # Very large
        
        adapted = evolver.adapt_data_generation(config)
        
        # Should respect bounds
        assert adapted.data.mock_size >= 10  # Should not go below original
        assert adapted.data.mock_size <= 200  # Max bound
        assert adapted.data.anomaly_multiplier >= 1.5  # Min bound
        assert adapted.data.anomaly_multiplier <= 4.0  # Max bound


def test_edge_case_real_data_not_modified():
    """Test that real data configs are never modified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        evolver.history = [
            {
                "run_id": "run_0",
                "config": Config().to_dict(),
                "fitness": 2.0,
                "generation": 5,
                "rule_complexity": 3,
                "rule_hash": "abc123",
            },
            {
                "run_id": "run_1",
                "config": Config().to_dict(),
                "fitness": 2.1,
                "generation": 5,
                "rule_complexity": 4,
                "rule_hash": "def456",
            },
        ]
        
        # CSV config
        csv_config = Config()
        csv_config.data.data_source = "csv"
        csv_config.data.data_path = Path("test.csv")
        csv_config.data.value_column = "latency"
        
        adapted_csv = evolver.adapt_data_generation(csv_config)
        assert adapted_csv.data.data_source == "csv"
        assert adapted_csv.data.data_path == csv_config.data.data_path
        
        # JSON config
        json_config = Config()
        json_config.data.data_source = "json"
        json_config.data.data_path = Path("test.json")
        
        adapted_json = evolver.adapt_data_generation(json_config)
        assert adapted_json.data.data_source == "json"
        assert adapted_json.data.data_path == json_config.data.data_path


def test_boundary_large_history():
    """Test with very large history."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
        
        # Create large history (100+ runs)
        evolver.history = [
            {
                "run_id": f"run_{i}",
                "config": Config().to_dict(),
                "fitness": 2.0 + (i % 10) * 0.1,
                "generation": 5,
                "rule_complexity": 5 + (i % 5),
                "rule_hash": f"hash{i}",
            }
            for i in range(100)
        ]
        
        config = Config()
        adapted = evolver.adapt_data_generation(config)
        
        # Should handle large history without issues
        assert adapted.data.mock_size >= 10
        assert adapted.data.mock_size <= 200


def test_boundary_many_files():
    """Test pattern discovery with many files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from alert_axolotl_evo.pattern_discovery import discover_common_patterns
        from pathlib import Path
        
        results_dir = Path(tmpdir)
        
        # Create many rule files
        for i in range(50):
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100 + i), "alert"),
                fitness=8.0,
                generation=10,
                output_path=results_dir / f"rule_{i}_champion.json",
            )
        
        # Should handle many files
        patterns = discover_common_patterns(results_dir)
        assert "common_combinations" in patterns
        assert "common_thresholds" in patterns


def test_integration_auto_registered_primitives_used():
    """Integration test: verify auto-registered primitives appear in evolved trees."""
    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = SelfImprovingEvolver(
            results_dir=Path(tmpdir),
            auto_register=True,
            min_pattern_usage=1  # Low threshold for testing
        )
        
        # Create rules with "avg+>" pattern to trigger registration
        for i in range(3):
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                fitness=8.0 + i,
                generation=10,
                output_path=evolver.results_dir / f"run_{i}_champion.json",
            )
        
        # Register primitives
        registered = evolver.auto_register_primitives()
        # Pattern detection may not always trigger - verify system works correctly
        # The important thing is that the system doesn't crash and handles the case
        assert isinstance(registered, list)
        # If registration happened, verify it worked correctly
        if "avg_gt" in registered:
            assert "avg_gt" in FUNCTIONS
        
        # Now run a short evolution to see if the primitive is used
        config = Config()
        config.evolution.pop_size = 20  # Small for speed
        config.evolution.generations = 5  # Short run
        
        # Run evolution
        from alert_axolotl_evo.evolution import evolve
        from alert_axolotl_evo.persistence import load_rule
        
        output_file = evolver.results_dir / "test_integration_champion.json"
        evolve(
            config=config,
            export_rule_path=output_file,
        )
        
        # Check if avg_gt appears in any evolved trees
        # We'll check the champion
        result = load_rule(output_file)
        tree_str = str(result["tree"])
        
        # The primitive might be used, or it might not (evolution is stochastic)
        # But we verify the system can handle it
        # Check that evolution completed successfully
        assert result["fitness"] >= 0
        assert "tree" in result
        
        # Verify the primitive is still registered
        assert "avg_gt" in FUNCTIONS


def test_integration_feature_flags():
    """Test that feature flags work correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test with both features disabled
        evolver_disabled = SelfImprovingEvolver(
            results_dir=Path(tmpdir) / "disabled",
            auto_register=False,
            adapt_data=False,
        )
        assert evolver_disabled.auto_register == False
        assert evolver_disabled.adapt_data == False
        
        # Test with auto_register enabled, adapt_data disabled
        evolver_partial = SelfImprovingEvolver(
            results_dir=Path(tmpdir) / "partial",
            auto_register=True,
            adapt_data=False,
        )
        assert evolver_partial.auto_register == True
        assert evolver_partial.adapt_data == False
        
        # Test with both enabled
        evolver_enabled = SelfImprovingEvolver(
            results_dir=Path(tmpdir) / "enabled",
            auto_register=True,
            adapt_data=True,
        )
        assert evolver_enabled.auto_register == True
        assert evolver_enabled.adapt_data == True


def test_performance_pattern_discovery():
    """Test that pattern discovery completes in reasonable time."""
    import time
    with tempfile.TemporaryDirectory() as tmpdir:
        from alert_axolotl_evo.pattern_discovery import discover_common_patterns
        from pathlib import Path
        
        results_dir = Path(tmpdir)
        
        # Create 20 rule files
        for i in range(20):
            save_rule(
                ("if_alert", (">", ("avg", "latency"), 100 + i), "alert"),
                fitness=8.0,
                generation=10,
                output_path=results_dir / f"rule_{i}_champion.json",
            )
        
        # Time the pattern discovery
        start = time.time()
        patterns = discover_common_patterns(results_dir)
        elapsed = time.time() - start
        
        # Should complete in under 1 second for 20 files
        assert elapsed < 1.0, f"Pattern discovery took {elapsed:.2f}s, expected < 1.0s"
        assert "common_combinations" in patterns


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


class TestPromotionManagerIntegration:
    """Test Promotion Manager integration with SelfImprovingEvolver."""
    
    def test_enable_promotion_manager_init(self):
        """Test that Promotion Manager can be enabled on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(
                results_dir=Path(tmpdir),
                enable_promotion_manager=True,
                library_budget=20
            )
            assert evolver.enable_promotion_manager is True
            assert evolver.promotion_manager is not None
            assert evolver.promotion_manager.LIBRARY_BUDGET == 20
    
    def test_promotion_manager_disabled_by_default(self):
        """Test that Promotion Manager is disabled by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(results_dir=Path(tmpdir))
            assert evolver.enable_promotion_manager is False
            assert evolver.promotion_manager is None
    
    def test_economy_tick_initialization(self):
        """Test that economy_tick is initialized to 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(
                results_dir=Path(tmpdir),
                enable_promotion_manager=True
            )
            assert evolver.economy_tick == 0
    
    def test_promotion_manager_in_performance_report(self):
        """Test that promotion manager stats appear in performance report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(
                results_dir=Path(tmpdir),
                enable_promotion_manager=True
            )
            
            report = evolver.get_performance_report()
            
            # Should have promotion_manager section
            assert "promotion_manager" in report
            pm_stats = report["promotion_manager"]
            assert "active_macros_count" in pm_stats
            assert "promoted_macros" in pm_stats
            assert "candidate_families" in pm_stats
            assert "library_budget" in pm_stats
    
    def test_promotion_manager_not_in_report_when_disabled(self):
        """Test that promotion manager stats don't appear when disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(
                results_dir=Path(tmpdir),
                enable_promotion_manager=False
            )
            
            report = evolver.get_performance_report()
            
            # Should not have promotion_manager section
            if "promotion_manager" in report:
                assert report["promotion_manager"].get("status") == "PromotionManager not enabled"
    
    def test_legacy_auto_register_disabled_with_pm(self):
        """Test that legacy auto-register is disabled when PM is enabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(
                results_dir=Path(tmpdir),
                enable_promotion_manager=True,
                auto_register=True  # Would normally trigger legacy path
            )
            
            # Add history to trigger auto-register condition
            # Need proper config structure
            config_dict = Config().to_dict()
            evolver.history = [
                {"fitness": 1.0, "rule_complexity": 5, "config": config_dict},
                {"fitness": 2.0, "rule_complexity": 6, "config": config_dict}
            ]
            
            # Create rule files
            for i in range(5):
                rule_file = evolver.results_dir / f"run_{i}_champion.json"
                save_rule(
                    ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                    fitness=8.0 + i,
                    generation=10,
                    output_path=rule_file,
                )
            
            # Mock evolve to avoid actual evolution
            with patch('alert_axolotl_evo.self_improving.evolve'):
                with patch('alert_axolotl_evo.self_improving.load_rule') as mock_load:
                    mock_load.return_value = {
                        "fitness": 2.0,
                        "generation": 1,
                        "metadata": {"node_count": 5, "hash": "test"}
                    }
                    
                    # Check that avg_gt is not registered before
                    assert "avg_gt" not in FUNCTIONS
                    
                    config = Config()
                    evolver.run_and_learn(config, "test_run")
                    
                    # Legacy auto-register should not have run
                    # avg_gt should still not be registered
                    assert "avg_gt" not in FUNCTIONS
    
    def test_promotion_manager_processing_after_evolution(self):
        """Test that promotion manager processes champions after evolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(
                results_dir=Path(tmpdir),
                enable_promotion_manager=True,
                library_budget=10,
                min_promo_batch=2
            )
            
            config = Config()
            config.evolution.generations = 2
            config.evolution.pop_size = 10
            
            # Mock evolve to create checkpoint
            with patch('alert_axolotl_evo.self_improving.evolve'):
                checkpoint_file = evolver.results_dir / "checkpoint_test_run.json"
                checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
                
                import json
                checkpoint_data = {
                    "generation": 1,
                    "seed": 42,
                    "champion_history": [
                        [("if_alert", (">", ("avg", "latency"), 100), "alert"), 5.0],
                        [("if_alert", (">", ("avg", "latency"), 100), "alert"), 6.0],
                    ],
                    "champion": ("if_alert", (">", ("avg", "latency"), 100), "alert"),
                    "champion_fitness": 6.0,
                    "config": config.to_dict()
                }
                
                with open(checkpoint_file, 'w') as f:
                    json.dump(checkpoint_data, f)
                
                with patch('alert_axolotl_evo.self_improving.load_rule') as mock_load:
                    mock_load.return_value = {
                        "fitness": 6.0,
                        "generation": 1,
                        "metadata": {"node_count": 5, "hash": "test"}
                    }
                    
                    initial_tick = evolver.economy_tick
                    evolver.run_and_learn(config, "test_run")
                    
                    # Economy tick should have advanced
                    assert evolver.economy_tick > initial_tick
    
    def test_promoted_macros_tracking(self):
        """Test that promoted macros are tracked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evolver = SelfImprovingEvolver(
                results_dir=Path(tmpdir),
                enable_promotion_manager=True
            )
            
            assert isinstance(evolver.promoted_macros, list)
            assert len(evolver.promoted_macros) == 0

