"""Meta-evolution: Evolve better evolution parameters."""

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.evolution import evolve
from alert_axolotl_evo.persistence import load_rule


@dataclass
class ConfigGenome:
    """Represents a configuration as a genome for meta-evolution."""
    pop_size: int
    mutation_rate: float
    crossover_rate: float
    tournament_size: int
    elite_ratio: float
    
    def to_config(self, base_config: Optional[Config] = None) -> Config:
        """Convert genome to Config object."""
        if base_config is None:
            config = Config()
        else:
            config = Config()
            # Copy base config values
            config.evolution.seed = base_config.evolution.seed
            config.evolution.generations = base_config.evolution.generations
            config.evolution.min_depth = base_config.evolution.min_depth
            config.evolution.max_depth = base_config.evolution.max_depth
            config.fitness = base_config.fitness
            config.data = base_config.data
        
        # Apply genome values
        config.evolution.pop_size = self.pop_size
        config.operators.mutation_rate = self.mutation_rate
        config.operators.crossover_rate = self.crossover_rate
        config.operators.tournament_size = self.tournament_size
        config.evolution.elite_ratio = self.elite_ratio
        
        return config
    
    @classmethod
    def random(cls, 
               pop_size_range: Tuple[int, int] = (20, 100),
               mutation_range: Tuple[float, float] = (0.1, 0.3),
               crossover_range: Tuple[float, float] = (0.7, 0.95),
               tournament_range: Tuple[int, int] = (2, 8),
               elite_range: Tuple[float, float] = (0.05, 0.2)) -> "ConfigGenome":
        """Create a random config genome."""
        return cls(
            pop_size=random.randint(*pop_size_range),
            mutation_rate=random.uniform(*mutation_range),
            crossover_rate=random.uniform(*crossover_range),
            tournament_size=random.randint(*tournament_range),
            elite_ratio=random.uniform(*elite_range),
        )
    
    def mutate(self, 
               pop_size_mutation: float = 0.1,
               rate_mutation: float = 0.05) -> "ConfigGenome":
        """Mutate this genome."""
        return ConfigGenome(
            pop_size=max(10, int(self.pop_size * (1 + random.uniform(-pop_size_mutation, pop_size_mutation)))),
            mutation_rate=max(0.05, min(0.5, self.mutation_rate + random.uniform(-rate_mutation, rate_mutation))),
            crossover_rate=max(0.5, min(1.0, self.crossover_rate + random.uniform(-rate_mutation, rate_mutation))),
            tournament_size=max(2, min(10, self.tournament_size + random.randint(-1, 1))),
            elite_ratio=max(0.05, min(0.3, self.elite_ratio + random.uniform(-rate_mutation, rate_mutation))),
        )
    
    @classmethod
    def crossover(cls, parent_a: "ConfigGenome", parent_b: "ConfigGenome") -> Tuple["ConfigGenome", "ConfigGenome"]:
        """Crossover two genomes."""
        # Uniform crossover
        child1 = cls(
            pop_size=parent_a.pop_size if random.random() < 0.5 else parent_b.pop_size,
            mutation_rate=parent_a.mutation_rate if random.random() < 0.5 else parent_b.mutation_rate,
            crossover_rate=parent_a.crossover_rate if random.random() < 0.5 else parent_b.crossover_rate,
            tournament_size=parent_a.tournament_size if random.random() < 0.5 else parent_b.tournament_size,
            elite_ratio=parent_a.elite_ratio if random.random() < 0.5 else parent_b.elite_ratio,
        )
        
        child2 = cls(
            pop_size=parent_b.pop_size if random.random() < 0.5 else parent_a.pop_size,
            mutation_rate=parent_b.mutation_rate if random.random() < 0.5 else parent_a.mutation_rate,
            crossover_rate=parent_b.crossover_rate if random.random() < 0.5 else parent_a.crossover_rate,
            tournament_size=parent_b.tournament_size if random.random() < 0.5 else parent_a.tournament_size,
            elite_ratio=parent_b.elite_ratio if random.random() < 0.5 else parent_a.elite_ratio,
        )
        
        return child1, child2


def evaluate_config_genome(genome: ConfigGenome, 
                           base_config: Optional[Config] = None,
                           eval_generations: int = 10,
                           eval_pop_size: Optional[int] = None) -> float:
    """
    Evaluate a configuration genome by running evolution.
    
    Args:
        genome: Configuration genome to evaluate
        base_config: Base configuration to inherit other settings from
        eval_generations: Number of generations for quick evaluation
        eval_pop_size: Override pop_size for faster evaluation (optional)
        
    Returns:
        Fitness score (best fitness achieved)
    """
    config = genome.to_config(base_config)
    
    # Use smaller pop_size for faster evaluation if specified
    if eval_pop_size:
        config.evolution.pop_size = eval_pop_size
    else:
        # Use smaller pop_size for evaluation to speed up
        config.evolution.pop_size = min(genome.pop_size, 30)
    
    config.evolution.generations = eval_generations
    
    # Run evolution with temporary output
    temp_output = Path("temp_meta_eval.json")
    try:
        evolve(config=config, export_rule_path=temp_output)
        
        # Load result
        if temp_output.exists():
            result = load_rule(temp_output)
            fitness = result.get("fitness", 0.0)
            temp_output.unlink()
            return fitness
        else:
            return 0.0
    except Exception:
        if temp_output.exists():
            temp_output.unlink()
        return 0.0


class MetaEvolver:
    """Evolves better evolution configurations."""
    
    def __init__(self, 
                 base_config: Optional[Config] = None,
                 pop_size: int = 10,
                 generations: int = 5,
                 eval_generations: int = 10):
        self.base_config = base_config or Config()
        self.pop_size = pop_size
        self.generations = generations
        self.eval_generations = eval_generations
        self.history: List[Tuple[ConfigGenome, float]] = []
    
    def evolve_configs(self) -> ConfigGenome:
        """
        Evolve better configurations.
        
        Returns:
            Best evolved configuration genome
        """
        # Initialize population
        population = [ConfigGenome.random() for _ in range(self.pop_size)]
        
        for gen in range(self.generations):
            # Evaluate all genomes
            scored = []
            for genome in population:
                fitness = evaluate_config_genome(
                    genome, 
                    self.base_config, 
                    self.eval_generations
                )
                scored.append((genome, fitness))
                self.history.append((genome, fitness))
            
            # Sort by fitness
            scored.sort(key=lambda x: -x[1])
            
            # Keep best as elite
            elite_count = max(1, self.pop_size // 4)
            elites = [genome for genome, _ in scored[:elite_count]]
            
            # Create next generation
            next_population = elites[:]
            
            while len(next_population) < self.pop_size:
                # Tournament selection
                parent_a = self._tournament_select(scored)
                parent_b = self._tournament_select(scored)
                
                # Crossover
                if random.random() < 0.7:
                    child1, child2 = ConfigGenome.crossover(parent_a, parent_b)
                else:
                    child1, child2 = parent_a, parent_b
                
                # Mutation
                if random.random() < 0.3:
                    child1 = child1.mutate()
                if random.random() < 0.3:
                    child2 = child2.mutate()
                
                next_population.extend([child1, child2])
            
            population = next_population[:self.pop_size]
            
            # Log progress
            best_genome, best_fitness = scored[0]
            print(f"Meta-Gen {gen}: Best fitness {best_fitness:.2f} "
                  f"(pop={best_genome.pop_size}, mut={best_genome.mutation_rate:.2f})")
        
        # Return best
        scored.sort(key=lambda x: -x[1])
        return scored[0][0]
    
    def _tournament_select(self, scored: List[Tuple[ConfigGenome, float]], size: int = 3) -> ConfigGenome:
        """Tournament selection."""
        contenders = random.sample(scored, min(size, len(scored)))
        contenders.sort(key=lambda x: -x[1])
        return contenders[0][0]
    
    def get_best_config(self) -> Config:
        """Get the best configuration found."""
        if not self.history:
            return self.base_config
        
        best_genome, _ = max(self.history, key=lambda x: x[1])
        return best_genome.to_config(self.base_config)

