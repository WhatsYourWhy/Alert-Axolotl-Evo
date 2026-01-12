"""Tests for fitness evaluation."""

import pytest

from alert_axolotl_evo.fitness import coerce_number, evaluate, fitness
from alert_axolotl_evo.config import FitnessConfig, DataConfig


def test_coerce_number():
    """Test number coercion."""
    assert coerce_number(5) == 5.0
    assert coerce_number(5.5) == 5.5
    assert coerce_number("5") == 0.0  # String not coerced
    assert coerce_number([1, 2, 3]) == 2.0  # Average


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
    assert fit >= 0  # Fitness should be non-negative or at least a number


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