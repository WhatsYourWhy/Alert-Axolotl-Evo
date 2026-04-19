"""Tests for evolution loop."""


from alert_axolotl_evo.config import Config
from alert_axolotl_evo.evolution import evolve, select_top_bottom


def test_select_top_bottom():
    """Test top/bottom selection."""
    trees = list(range(10))
    selected = select_top_bottom(trees, count=2)
    assert len(selected) == 4  # Top 2 + bottom 2
    assert selected[0] == 0
    assert selected[1] == 1
    assert selected[2] == 8
    assert selected[3] == 9


def test_evolve_deterministic():
    """Test that evolution is deterministic with same seed."""
    config = Config()
    config.evolution.seed = 42
    config.evolution.pop_size = 10
    config.evolution.generations = 2
    
    # This is a basic smoke test - just verify it runs
    # Full deterministic testing would require more setup
    evolve(config=config)

