"""Persistence: save/load rules and checkpoints."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from alert_axolotl_evo.tree import node_count, tree_hash


def save_rule(
    tree: Any,
    fitness: float,
    generation: int,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save an evolved rule to JSON file.
    
    Args:
        tree: The evolved tree/rule
        fitness: Fitness score
        generation: Generation number
        output_path: Path to save the rule
        metadata: Additional metadata to include
    """
    rule_data = {
        "tree": tree,
        "fitness": fitness,
        "generation": generation,
        "metadata": {
            "hash": tree_hash(tree),
            "node_count": node_count(tree),
            "created_at": datetime.now().isoformat(),
            **(metadata or {}),
        },
    }
    
    with open(output_path, "w") as f:
        json.dump(rule_data, f, indent=2)


def load_rule(input_path: Path) -> Dict[str, Any]:
    """
    Load a rule from JSON file.
    
    Args:
        input_path: Path to the rule file
        
    Returns:
        Dictionary with 'tree', 'fitness', 'generation', and 'metadata'
    """
    with open(input_path, "r") as f:
        return json.load(f)


def save_checkpoint(
    population: List[Any],
    generation: int,
    seed: int,
    champion: Any,
    champion_fitness: float,
    champion_history: List[Tuple[Any, float]],
    output_path: Path,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save evolution checkpoint.
    
    Args:
        population: Current population
        generation: Current generation number
        seed: Random seed
        champion: Current champion tree
        champion_fitness: Champion fitness
        champion_history: List of (tree, fitness) tuples for champion history
        output_path: Path to save checkpoint
        config: Configuration dictionary
    """
    checkpoint_data = {
        "generation": generation,
        "seed": seed,
        "population": population,
        "champion": champion,
        "champion_fitness": champion_fitness,
        "champion_history": [(tree, fit) for tree, fit in champion_history],
        "config": config,
        "created_at": datetime.now().isoformat(),
    }
    
    with open(output_path, "w") as f:
        json.dump(checkpoint_data, f, indent=2)


def load_checkpoint(input_path: Path) -> Dict[str, Any]:
    """
    Load evolution checkpoint.
    
    Args:
        input_path: Path to checkpoint file
        
    Returns:
        Dictionary with checkpoint data
    """
    with open(input_path, "r") as f:
        return json.load(f)

