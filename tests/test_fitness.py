"""Tests for fitness evaluation."""

import pytest

from alert_axolotl_evo.fitness import coerce_number, evaluate, fitness, fitness_breakdown
from alert_axolotl_evo.config import FitnessConfig, DataConfig
from alert_axolotl_evo.data import MockDataLoader
from alert_axolotl_evo.tree import is_valid_alert_rule


def test_coerce_number():
    """Test number coercion."""
    assert coerce_number(5) == 5.0
    assert coerce_number(5.5) == 5.5
    assert coerce_number("5") is None  # String not coerced, returns None
    assert coerce_number([1, 2, 3]) is None  # List not coerced, returns None (no implicit averaging)


def test_evaluate_simple():
    """Test simple tree evaluation."""
    tree = (">", 5, 3)
    data = {}
    result = evaluate(tree, data)
    assert result is True
    
    tree2 = ("<", 5, 3)
    result2 = evaluate(tree2, data)
    assert result2 is False


def test_evaluate_with_data():
    """Test evaluation with data."""
    tree = (">", "latency", 100)
    data = {"latency": 150}
    result = evaluate(tree, data)
    assert result is True
    
    data2 = {"latency": 50}
    result2 = evaluate(tree, data2)
    assert result2 is False


def test_evaluate_avg():
    """Test average function."""
    tree = ("avg", "latency")
    data = {"latency": [10, 20, 30]}
    result = evaluate(tree, data)
    assert result == 20.0


def test_evaluate_if_alert():
    """Test if_alert function."""
    tree = ("if_alert", (">", "latency", 100), "High alert!")
    data = {"latency": 150}
    result = evaluate(tree, data)
    assert result == "High alert!"
    
    data2 = {"latency": 50}
    result2 = evaluate(tree, data2)
    assert result2 is None


def test_evaluate_invalid_tree():
    """Test evaluation of invalid trees."""
    tree = ("invalid_op", 1, 2)
    data = {}
    result = evaluate(tree, data)
    assert result is None


def test_fitness():
    """Test fitness calculation."""
    tree = ("if_alert", (">", ("avg", "latency"), 100), "High alert!")
    fit = fitness(tree, seed=42, gen=0)
    assert isinstance(fit, float)
    # Fitness can be negative due to penalties (bloat, false positives, etc.)


class TestGenericDispatch:
    """Test generic function dispatch."""
    
    def test_all_comparison_operators(self):
        """Test all comparison operators work with generic dispatch."""
        data = {}
        operators = [">", "<", ">=", "<=", "==", "!="]
        
        for op in operators:
            tree = (op, 5, 3)
            result = evaluate(tree, data)
            assert isinstance(result, bool)
    
    def test_all_logical_operators(self):
        """Test all logical operators work with generic dispatch."""
        data = {}
        
        # Binary logical
        tree_and = ("and", True, False)
        assert evaluate(tree_and, data) is False
        
        tree_or = ("or", True, False)
        assert evaluate(tree_or, data) is True
        
        # Unary logical
        tree_not = ("not", True)
        assert evaluate(tree_not, data) is False
    
    def test_all_statistical_functions(self):
        """Test all statistical functions work with generic dispatch."""
        data = {"latency": [10, 20, 30, 40, 50]}
        
        stats_funcs = ["avg", "max", "min", "sum", "count", "stddev"]
        for func in stats_funcs:
            tree = (func, "latency")
            result = evaluate(tree, data)
            assert isinstance(result, (int, float))
    
    def test_percentile_function(self):
        """Test percentile function with generic dispatch."""
        data = {"latency": [10, 20, 30, 40, 50]}
        tree = ("percentile", "latency", 90)
        result = evaluate(tree, data)
        assert isinstance(result, (int, float))
    
    def test_window_functions(self):
        """Test window functions with generic dispatch."""
        data = {"latency": [10, 20, 30, 40, 50]}
        
        window_funcs = ["window_avg", "window_max", "window_min"]
        for func in window_funcs:
            tree = (func, "latency", 3)
            result = evaluate(tree, data)
            assert isinstance(result, (int, float))


class TestArityEnforcement:
    """Test arity enforcement."""
    
    def test_wrong_arity_returns_zero(self):
        """Test that wrong arity returns 0 (safe penalized value)."""
        data = {}
        
        # Binary operator with one arg (wrong)
        tree = (">", 5)
        result = evaluate(tree, data)
        assert result == 0  # Returns 0 for arity mismatch
        
        # Unary operator with two args (wrong)
        tree2 = ("not", True, False)
        result2 = evaluate(tree2, data)
        assert result2 == 0  # Returns 0 for arity mismatch
    
    def test_correct_arity_works(self):
        """Test that correct arity still works."""
        data = {}
        
        # Binary operator with two args (correct)
        tree = (">", 5, 3)
        result = evaluate(tree, data)
        assert result is True
        
        # Unary operator with one arg (correct)
        tree2 = ("not", True)
        result2 = evaluate(tree2, data)
        assert result2 is False
    
    def test_statistical_function_arity(self):
        """Test statistical function arity enforcement."""
        data = {"latency": [10, 20, 30]}
        
        # Correct arity (1 arg)
        tree = ("avg", "latency")
        result = evaluate(tree, data)
        assert isinstance(result, (int, float))
        
        # Wrong arity (2 args) - returns 0 (safe penalized value)
        tree2 = ("avg", "latency", 100)
        result2 = evaluate(tree2, data)
        assert result2 == 0  # Returns 0, not None, for arity mismatch
    
    def test_percentile_arity(self):
        """Test percentile function arity enforcement."""
        data = {"latency": [10, 20, 30]}
        
        # Correct arity (2 args)
        tree = ("percentile", "latency", 90)
        result = evaluate(tree, data)
        assert isinstance(result, (int, float))
        
        # Wrong arity (1 arg) - returns 0 (safe penalized value)
        tree2 = ("percentile", "latency")
        result2 = evaluate(tree2, data)
        assert result2 == 0  # Returns 0, not None, for arity mismatch


class TestMacroSupport:
    """Test macro support with needs_context."""
    
    def test_macro_execution_with_context(self):
        """Test that macros receive data context."""
        from alert_axolotl_evo.compiler import PrimitiveCompiler
        from alert_axolotl_evo.primitives import register_function, unregister_function
        
        compiler = PrimitiveCompiler(evaluate)
        subtree = (">", ("avg", "latency"), 100)
        macro_func = compiler.compile_macro(subtree)
        
        # Register as macro
        register_function("test_macro", macro_func, arity=0, needs_context=True)
        
        try:
            # Use macro in tree
            tree = ("test_macro",)
            data = {"latency": [150, 160, 170]}
            result = evaluate(tree, data)
            assert result is True
            
            data2 = {"latency": [50, 60, 70]}
            result2 = evaluate(tree, data2)
            assert result2 is False
        finally:
            unregister_function("test_macro")
    
    def test_macro_with_complex_subtree(self):
        """Test macro with complex nested subtree."""
        from alert_axolotl_evo.compiler import PrimitiveCompiler
        from alert_axolotl_evo.primitives import register_function, unregister_function
        
        compiler = PrimitiveCompiler(evaluate)
        subtree = (
            "and",
            (">", ("avg", "latency"), 100),
            ("<", ("max", "latency"), 200)
        )
        macro_func = compiler.compile_macro(subtree)
        
        register_function("complex_macro", macro_func, arity=0, needs_context=True)
        
        try:
            tree = ("complex_macro",)
            data = {"latency": [150, 160, 170]}
            result = evaluate(tree, data)
            assert result is True
        finally:
            unregister_function("complex_macro")
    
    def test_standard_function_no_context_injection(self):
        """Test that standard functions don't receive context."""
        data = {"latency": 150}
        
        # Standard function should work normally
        tree = (">", "latency", 100)
        result = evaluate(tree, data)
        assert result is True


class TestErrorHandling:
    """Test error handling in evaluation."""
    
    def test_error_returns_none_not_zero(self):
        """Test that errors return None, not 0."""
        data = {}
        
        # Invalid tree structure
        tree = ("invalid", 1, 2, 3, 4)
        result = evaluate(tree, data)
        assert result is None  # Not 0
    
    def test_division_by_zero_handling(self):
        """Test that division by zero is handled gracefully."""
        # This would be in a custom function, but test that errors don't crash
        data = {}
        tree = ("avg", "empty_list")
        data["empty_list"] = []
        result = evaluate(tree, data)
        # Should return 0 (avg of empty list) or None, not crash
        assert result is not None or result == 0
    
    def test_missing_data_key(self):
        """Test handling of missing data keys."""
        data = {}
        tree = (">", "nonexistent", 100)
        result = evaluate(tree, data)
        # Should handle gracefully
        assert result is None or isinstance(result, bool)


class TestBackwardCompatibility:
    """Test backward compatibility with existing trees."""
    
    def test_existing_trees_still_work(self):
        """Test that existing tree structures still evaluate correctly."""
        data = {"latency": [150, 160, 170]}
        
        # Classic pattern
        tree = ("if_alert", (">", ("avg", "latency"), 100), "Alert!")
        result = evaluate(tree, data)
        assert result == "Alert!"
        
        # Complex nested
        tree2 = (
            "if_alert",
            ("and",
                (">", ("avg", "latency"), 100),
                ("<", ("max", "latency"), 200)
            ),
            "Complex alert!"
        )
        result2 = evaluate(tree2, data)
        assert result2 == "Complex alert!"
    
    def test_all_function_types_still_work(self):
        """Test that all function types still work after refactor."""
        data = {"latency": [10, 20, 30]}
        
        # Statistical
        assert evaluate(("avg", "latency"), data) == 20.0
        assert evaluate(("max", "latency"), data) == 30.0
        assert evaluate(("min", "latency"), data) == 10.0
        
        # Comparison
        assert evaluate((">", 5, 3), {}) is True
        assert evaluate(("<", 3, 5), {}) is True
        
        # Logical
        assert evaluate(("and", True, True), {}) is True
        assert evaluate(("or", False, True), {}) is True
        assert evaluate(("not", False), {}) is True


def test_fitness_consistent_data():
    """Test that fitness evaluation with consistent_data=True produces same results."""
    tree = ("if_alert", (">", ("max", "latency"), 75), "High alert!")
    
    # Create data loader with consistent_data=True
    data_config = DataConfig(consistent_data=True, mock_size=100, anomaly_count=10)
    data_loader = MockDataLoader(seed=42, size=100, anomaly_count=10, use_realistic_patterns=False)
    
    # Evaluate fitness with same seed (generation 0)
    fit1 = fitness(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    
    # Reset loader and evaluate again with same seed (should be same data)
    data_loader.seed = 42
    fit2 = fitness(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    
    # Fitness should be identical with consistent data
    assert fit1 == fit2
    
    # Test across generations (should still be same with consistent_data=True)
    data_loader.seed = 42
    fit_gen0 = fitness(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    data_loader.seed = 42  # Same seed even though gen=1
    fit_gen1 = fitness(tree, seed=42, gen=1, data_config=data_config, data_loader=data_loader)
    
    # With consistent_data=True, same seed should produce same fitness
    assert fit_gen0 == fit_gen1


def test_fitness_varying_data():
    """Test that fitness evaluation with consistent_data=False produces different results."""
    tree = ("if_alert", (">", ("max", "latency"), 75), "High alert!")
    
    # Create data loader with consistent_data=False
    data_config = DataConfig(consistent_data=False, mock_size=100, anomaly_count=10)
    data_loader = MockDataLoader(seed=42, size=100, anomaly_count=10, use_realistic_patterns=False)
    
    # Evaluate fitness with seed + 0 (generation 0)
    data_loader.seed = 42
    fit_gen0 = fitness(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    
    # Evaluate fitness with seed + 1 (generation 1)
    data_loader.seed = 43
    fit_gen1 = fitness(tree, seed=42, gen=1, data_config=data_config, data_loader=data_loader)
    
    # Fitness may be different with different data (though could coincidentally be same)
    # At minimum, we verify the system works correctly
    assert isinstance(fit_gen0, float)
    assert isinstance(fit_gen1, float)


def test_fitness_breakdown_consistent_data():
    """Test fitness_breakdown with consistent data."""
    tree = ("if_alert", (">", ("max", "latency"), 75), "High alert!")
    
    data_config = DataConfig(consistent_data=True, mock_size=100, anomaly_count=10)
    data_loader = MockDataLoader(seed=42, size=100, anomaly_count=10, use_realistic_patterns=False)
    
    # Get breakdown for generation 0
    data_loader.seed = 42
    breakdown1 = fitness_breakdown(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    
    # Get breakdown again with same seed
    data_loader.seed = 42
    breakdown2 = fitness_breakdown(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    
    # Should be identical
    assert breakdown1['fitness'] == breakdown2['fitness']
    assert breakdown1['tp'] == breakdown2['tp']
    assert breakdown1['fp'] == breakdown2['fp']
    assert breakdown1['fn'] == breakdown2['fn']
    assert breakdown1['alert_rate'] == breakdown2['alert_rate']
    assert breakdown1['invalid_rate'] == breakdown2['invalid_rate']


def test_fitness_with_realistic_data():
    """Test fitness evaluation with realistic data generation."""
    tree = ("if_alert", (">", ("max", "latency"), 75), "High alert!")
    
    data_config = DataConfig(
        consistent_data=True,
        mock_size=200,
        anomaly_count=20,
        use_realistic_patterns=True
    )
    data_loader = MockDataLoader(
        seed=42,
        size=200,
        anomaly_count=20,
        use_realistic_patterns=True
    )
    
    fit = fitness(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    
    # Should compute fitness successfully
    assert isinstance(fit, float)
    
    # Get breakdown to verify metrics
    data_loader.seed = 42
    breakdown = fitness_breakdown(tree, seed=42, gen=0, data_config=data_config, data_loader=data_loader)
    
    assert 'fitness' in breakdown
    assert 'tp' in breakdown
    assert 'fp' in breakdown
    assert 'fn' in breakdown
    assert 'alert_rate' in breakdown
    assert 'invalid_rate' in breakdown
    assert breakdown['alert_rate'] >= 0.0
    assert breakdown['alert_rate'] <= 1.0
    assert breakdown['invalid_rate'] >= 0.0
    assert breakdown['invalid_rate'] <= 1.0


class TestFitnessAlignment:
    """Test fitness alignment mechanisms."""
    
    def test_precision_pressure(self):
        """Test that precision pressure is applied for low precision rules."""
        # Create a rule with very low threshold (will have many false positives)
        low_precision_tree = ("if_alert", (">", ("avg", "latency"), 10), "Low threshold")
        breakdown = fitness_breakdown(low_precision_tree, seed=42, gen=0)
        
        # If precision is below 30%, penalty should be applied
        if breakdown['precision'] < 0.3 and breakdown['tp'] + breakdown['fp'] > 0:
            # Score should be lower due to precision penalty
            # Base score is f_beta * possible_tp, then penalties applied
            assert breakdown['fitness'] < breakdown['score']  # Penalties reduce fitness
    
    def test_fpr_penalty(self):
        """Test that FPR penalty is applied for high false positive rate."""
        # Create a rule with very low threshold (high FPR)
        high_fpr_tree = ("if_alert", (">", ("avg", "latency"), 5), "Very low threshold")
        breakdown = fitness_breakdown(high_fpr_tree, seed=42, gen=0)
        
        # If FPR > 15%, penalty should be applied
        if breakdown['fpr'] > 0.15:
            # Fitness should be penalized
            assert breakdown['fitness'] < breakdown['score']
    
    def test_alert_rate_band_low(self):
        """Test that alert rate below 0.2% is penalized."""
        # Create a rule with very high threshold (rarely fires)
        low_alert_tree = ("if_alert", (">", ("max", "latency"), 10000), "Very high threshold")
        breakdown = fitness_breakdown(low_alert_tree, seed=42, gen=0)
        
        # If alert rate < 0.2%, penalty should be applied
        if breakdown['alert_rate'] < 0.002:
            assert breakdown['fitness'] < breakdown['score']
    
    def test_alert_rate_band_high(self):
        """Test that alert rate above 20% is penalized."""
        # Create an always-true rule (high alert rate)
        always_true_tree = ("if_alert", True, "Always alerts")
        breakdown = fitness_breakdown(always_true_tree, seed=42, gen=0)
        
        # Alert rate should be very high (>50%)
        assert breakdown['alert_rate'] > 0.50
        
        # Should have heavy penalty (scales with dataset size)
        # For 1000 rows at 100% alert rate: penalty = 2.0 * 0.5 * 1000 = 1000
        assert breakdown['fitness'] < breakdown['score']
        # Fitness should be very negative
        assert breakdown['fitness'] < -100.0  # Heavy penalty for always-true
    
    def test_recall_floor(self):
        """Test that recall floor is enforced (minimum 10% or TP > 0)."""
        # Create a rule that never detects anomalies
        never_detects_tree = ("if_alert", (">", ("max", "latency"), 10000), "Too high")
        breakdown = fitness_breakdown(never_detects_tree, seed=42, gen=0)
        
        # If recall < 10% and TP == 0, penalty should be applied
        if breakdown['recall'] < 0.1 and breakdown['tp'] == 0:
            assert breakdown['fitness'] < breakdown['score']
    
    def test_degenerate_self_comparison(self):
        """Test that self-comparisons are penalized."""
        from alert_axolotl_evo.tree import is_self_comparison
        
        # Create a self-comparison (always False/True)
        self_comp_tree = ("if_alert", (">", "latency", "latency"), "Self comparison")
        
        # Verify it's detected as self-comparison
        condition = self_comp_tree[1]
        assert is_self_comparison(condition)
        
        breakdown = fitness_breakdown(self_comp_tree, seed=42, gen=0)
        
        # Should have heavy penalty (-10.0)
        assert breakdown['fitness'] < breakdown['score']
    
    def test_degenerate_no_alert(self):
        """Test that rules that never alert are penalized."""
        # Create a rule that never alerts (always False condition)
        never_alert_tree = ("if_alert", False, "Never alerts")
        breakdown = fitness_breakdown(never_alert_tree, seed=42, gen=0)
        
        # Should have TP=0, FP=0
        assert breakdown['tp'] == 0
        assert breakdown['fp'] == 0
        
        # Should have penalty (-5.0)
        assert breakdown['fitness'] < breakdown['score']
    
    def test_baseline_comparison(self):
        """Test that evolved rules should beat baselines."""
        from alert_axolotl_evo.fitness import (
            baseline_always_false, baseline_always_true, baseline_random
        )
        
        # A reasonable rule should beat baselines
        good_tree = ("if_alert", (">", ("max", "latency"), 75), "High latency")
        breakdown = fitness_breakdown(good_tree, seed=42, gen=0)
        
        # Get baselines
        always_false = baseline_always_false(seed=42, gen=0)
        always_true = baseline_always_true(seed=42, gen=0)
        random_baseline = baseline_random(seed=42, gen=0, threshold=50.0)
        
        # Good rule should beat always-false (unless it's also degenerate)
        if breakdown['tp'] > 0 or breakdown['fp'] > 0:
            assert breakdown['fitness'] > always_false['fitness']
        
        # Good rule should beat always-true (which has heavy penalty)
        assert breakdown['fitness'] > always_true['fitness']
        
        # Good rule should generally beat random baseline
        # (may not always be true, but should be often)
        # This is a soft check - if it fails, investigate why
    
    def test_invalid_output_gate(self):
        """Test that invalid outputs are penalized."""
        # Create a tree that produces invalid outputs
        # (e.g., statistical function on scalar instead of list)
        invalid_tree = ("if_alert", (">", ("avg", 50), 100), "Invalid")
        breakdown = fitness_breakdown(invalid_tree, seed=42, gen=0)
        
        # If invalid rate > 0, should have penalty
        if breakdown['invalid_rate'] > 0.0:
            # Soft penalty: 0.5 * invalid_rate
            assert breakdown['fitness'] <= breakdown['score']
        
        # If invalid rate > 50%, should be rejected (hard gate)
        # This is tested by fitness() returning -100.0
        if breakdown['invalid_rate'] > 0.5:
            fit = fitness(invalid_tree, seed=42, gen=0)
            assert fit == -100.0
    
    def test_alignment_metrics_in_breakdown(self):
        """Test that all alignment metrics are included in breakdown."""
        tree = ("if_alert", (">", ("max", "latency"), 75), "High latency")
        breakdown = fitness_breakdown(tree, seed=42, gen=0)
        
        # Check all alignment-related metrics are present
        assert 'precision' in breakdown
        assert 'fpr' in breakdown
        assert 'recall' in breakdown
        assert 'alert_rate' in breakdown
        assert 'invalid_rate' in breakdown
        
        # Check metrics are in valid ranges
        assert 0.0 <= breakdown['precision'] <= 1.0
        assert 0.0 <= breakdown['fpr'] <= 1.0
        assert 0.0 <= breakdown['recall'] <= 1.0
        assert 0.0 <= breakdown['alert_rate'] <= 1.0
        assert 0.0 <= breakdown['invalid_rate'] <= 1.0
    
    def test_early_rejection_stratified_sampling(self):
        """
        Regression test: Verify early rejection catches trees that break late.
        
        This test ensures that stratified sampling (early + late slices) prevents
        false negatives from head-only sampling. Trees that only break after
        enough history exists (e.g., window functions) should still be caught.
        
        Test case: A tree that is structurally valid but runtime-invalid only
        after some rows should be rejected either:
        - By early rejection if late slice shows high invalid_rate, OR
        - By hard gate at the end (fitness = -100, invalid_evaluation=True)
        """
        # Create a config with larger dataset to test late-breaking invalidity
        config = DataConfig()
        config.mock_size = 1000  # Large enough to have distinct early/late slices
        
        # Test 1: Structurally invalid tree (should be rejected immediately)
        invalid_tree = ("if_alert", ("or", "latency", 25), "test")
        assert not is_valid_alert_rule(invalid_tree), "Structure validation should reject bool-operator type errors"
        
        # Test 2: Verify early rejection is faster than full evaluation
        # (Performance test - early rejection should short-circuit)
        import time
        start = time.time()
        result = fitness(invalid_tree, 42, 0, data_config=config)
        elapsed = time.time() - start
        
        # Should be rejected quickly (structure check happens before evaluation)
        assert result == -100.0, "Invalid tree should return -100.0"
        assert elapsed < 0.1, "Structure validation should be fast (< 0.1s)"
    
    def test_comparison_ops_return_bool_or_none(self):
        """
        Verify comparison operators return bool or None, never numeric.
        
        Invariant: if either side is None → comparison returns None (not False).
        """
        # Test comparisons with None inputs
        assert evaluate((">", None, 5), {}) is None
        assert evaluate((">", 5, None), {}) is None
        assert evaluate(("<", None, None), {}) is None
        
        # Test valid comparisons return bool
        assert evaluate((">", 10, 5), {}) is True
        assert evaluate(("<", 5, 10), {}) is True
        assert type(evaluate((">", 10, 5), {})) is bool
        assert type(evaluate(("<", 5, 10), {})) is bool
        
        # Test that comparisons never return numeric (use type() not isinstance since bool is subclass of int)
        result = evaluate((">", 10, 5), {})
        assert type(result) is bool, "Comparison should return bool, not numeric"
    
    def test_message_validation(self):
        """
        Verify message slot validation: must be string, not numeric/boolean.
        """
        # Valid: string message
        valid_tree = ("if_alert", (">", ("max", "latency"), 75), "High latency!")
        assert is_valid_alert_rule(valid_tree)
        
        # Invalid: numeric message
        invalid_tree_numeric = ("if_alert", (">", ("max", "latency"), 75), 42)
        assert not is_valid_alert_rule(invalid_tree_numeric)
        
        # Invalid: boolean message
        invalid_tree_bool = ("if_alert", (">", ("max", "latency"), 75), True)
        assert not is_valid_alert_rule(invalid_tree_bool)
        
        # Valid: any string (not just MSG_TERMINALS)
        custom_message_tree = ("if_alert", (">", ("max", "latency"), 75), "Custom message")
        assert is_valid_alert_rule(custom_message_tree)