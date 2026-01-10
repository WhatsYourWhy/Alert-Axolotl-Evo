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

