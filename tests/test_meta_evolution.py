"""Tests for meta-evolution module."""

import pytest

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.meta_evolution import ConfigGenome, MetaEvolver


def test_config_genome_random():
    """Test random genome creation."""
    genome = ConfigGenome.random()
    assert 20 <= genome.pop_size <= 100
    assert 0.1 <= genome.mutation_rate <= 0.3
    assert 0.7 <= genome.crossover_rate <= 0.95


def test_config_genome_to_config():
    """Test genome to config conversion."""
    genome = ConfigGenome(
        pop_size=50,
        mutation_rate=0.2,
        crossover_rate=0.9,
        tournament_size=4,
        elite_ratio=0.1,
    )
    
    config = genome.to_config()
    assert config.evolution.pop_size == 50
    assert config.operators.mutation_rate == 0.2
    assert config.operators.crossover_rate == 0.9
    assert config.operators.tournament_size == 4
    assert config.evolution.elite_ratio == 0.1


def test_config_genome_mutate():
    """Test genome mutation."""
    genome = ConfigGenome(
        pop_size=50,
        mutation_rate=0.2,
        crossover_rate=0.9,
        tournament_size=4,
        elite_ratio=0.1,
    )
    
    mutated = genome.mutate()
    assert mutated.pop_size != genome.pop_size or mutated.mutation_rate != genome.mutation_rate
    # Values should still be in valid ranges
    assert mutated.pop_size >= 10
    assert 0.05 <= mutated.mutation_rate <= 0.5


def test_config_genome_crossover():
    """Test genome crossover."""
    parent_a = ConfigGenome(50, 0.2, 0.9, 4, 0.1)
    parent_b = ConfigGenome(100, 0.3, 0.8, 6, 0.15)
    
    child1, child2 = ConfigGenome.crossover(parent_a, parent_b)
    
    # Children should have some traits from parents
    assert isinstance(child1, ConfigGenome)
    assert isinstance(child2, ConfigGenome)
    # At least one child should differ from both parents
    assert (child1.pop_size != parent_a.pop_size or 
            child1.mutation_rate != parent_a.mutation_rate or
            child2.pop_size != parent_b.pop_size)


def test_meta_evolver():
    """Test meta-evolver initialization."""
    base_config = Config()
    evolver = MetaEvolver(
        base_config=base_config,
        pop_size=5,
        generations=2,
        eval_generations=3,
    )
    
    assert evolver.base_config == base_config
    assert evolver.pop_size == 5
    assert len(evolver.history) == 0

