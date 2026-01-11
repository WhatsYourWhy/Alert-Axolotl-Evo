"""Evolution loop and population management."""

import logging
import random
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from alert_axolotl_evo.config import Config
from alert_axolotl_evo.data import DataLoader, create_data_loader
from alert_axolotl_evo.fitness import fitness
from alert_axolotl_evo.operators import (
    initialize_population,
    point_mutation,
    subtree_crossover,
    tournament_select,
)
from alert_axolotl_evo.persistence import load_checkpoint, save_checkpoint, save_rule
from alert_axolotl_evo.tree import node_count
from alert_axolotl_evo.visualization import announce_birth, log_funeral, print_ascii_tree, generate_name


def select_top_bottom(trees: Sequence[Any], count: int = 3) -> List[Any]:
    """Select top and bottom trees for announcements."""
    if len(trees) <= count * 2:
        return list(trees)
    return list(trees[:count]) + list(trees[-count:])


def evolve(
    seed: Optional[int] = None,
    pop_size: Optional[int] = None,
    generations: Optional[int] = None,
    config: Optional[Config] = None,
    checkpoint_path: Optional[Path] = None,
    save_checkpoint_path: Optional[Path] = None,
    export_rule_path: Optional[Path] = None,
) -> None:
    """Main evolution loop."""
    if config is None:
        config = Config()
    
    # Use config values, but allow override via parameters for backward compatibility
    seed = seed if seed is not None else config.evolution.seed
    pop_size = pop_size if pop_size is not None else config.evolution.pop_size
    generations = generations if generations is not None else config.evolution.generations
    
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    # Create data loader
    try:
        data_loader = create_data_loader(config.data)
    except Exception as e:
        logging.getLogger("evo").warning(f"Failed to create data loader: {e}. Using mock data.")
        from alert_axolotl_evo.data import MockDataLoader
        data_loader = MockDataLoader(
            seed=seed,
            size=config.data.mock_size,
            anomaly_count=config.data.anomaly_count,
            anomaly_multiplier=config.data.anomaly_multiplier,
        )
    
    # Load checkpoint if provided
    start_gen = 0
    champion_history: List[Tuple[Any, float]] = []
    
    if checkpoint_path and checkpoint_path.exists():
        checkpoint = load_checkpoint(checkpoint_path)
        population = checkpoint["population"]
        start_gen = checkpoint["generation"] + 1
        seed = checkpoint["seed"]
        champion_history = [(tree, fit) for tree, fit in checkpoint.get("champion_history", [])]
        logging.getLogger("evo").info(f"Loaded checkpoint from generation {checkpoint['generation']}, resuming from generation {start_gen}")
    else:
        random.seed(seed)
        population = initialize_population(
            pop_size,
            config.evolution.min_depth,
            config.evolution.max_depth,
        )
        for tree in select_top_bottom(population):
            announce_birth(tree)

    champion = None
    champ_fit = 0.0
    for gen in range(start_gen, generations):
        logging.getLogger("evo").info("\n=== Generation %s ===", gen)
        scored = []
        for tree in population:
            fit = fitness(tree, seed, gen, config.fitness, config.data, data_loader)
            scored.append((tree, fit))

        scored.sort(key=lambda item: (-item[1], node_count(item[0])))
        champion, champ_fit = scored[0]
        
        # Update champion history
        if not champion_history or champ_fit > champion_history[-1][1]:
            champion_history.append((champion, champ_fit))
        
        for tree, fit in scored[:3]:
            name = generate_name(tree)
            logging.getLogger("evo").info("%s faces the anomaly horde... fitness %.2f", name, fit)
        logging.getLogger("evo").info("→ 🐉 ROARS VICTORIOUSLY!")
        print(print_ascii_tree(champion))
        if champ_fit > 0.9:
            logging.getLogger("evo").info("💥⚡🌟🔥 *CRASH* Anomaly detected! 🌟🔥⚡💥")
        
        # Save checkpoint if requested
        if save_checkpoint_path:
            save_checkpoint(
                population,
                gen,
                seed,
                champion,
                champ_fit,
                champion_history,
                save_checkpoint_path,
                config.to_dict(),
            )

        elites_count = max(1, int(config.evolution.elite_ratio * pop_size))
        elites = [tree for tree, _ in scored[:elites_count]]
        for tree, _ in scored[elites_count:][-2:]:
            log_funeral(tree, gen)

        next_population = elites[:]
        while len(next_population) < pop_size:
            parent_a = tournament_select(scored, config.operators.tournament_size)
            parent_b = tournament_select(scored, config.operators.tournament_size)
            if random.random() < config.operators.crossover_rate:
                child_a, child_b = subtree_crossover(parent_a, parent_b)
            else:
                child_a, child_b = parent_a, parent_b
            if random.random() < config.operators.mutation_rate:
                child_a = point_mutation(child_a, config.evolution.max_depth)
            if random.random() < config.operators.mutation_rate:
                child_b = point_mutation(child_b, config.evolution.max_depth)
            next_population.extend([child_a, child_b])

        population = next_population[:pop_size]
        for tree in select_top_bottom(population):
            announce_birth(tree)

    final_name = generate_name(champion)
    logging.getLogger("evo").info("\nFinal Champion: %s", final_name)
    logging.getLogger("evo").info("Final Champion Tree: %s", champion)
    logging.getLogger("evo").info("Final Champion Fitness: %.2f", champ_fit)
    print(print_ascii_tree(champion))
    
    # Export rule if requested
    if export_rule_path:
        save_rule(champion, champ_fit, generations - 1, export_rule_path)
        logging.getLogger("evo").info(f"Champion rule exported to {export_rule_path}")
    
    logging.getLogger("evo").info("Evolution complete. The fittest guardian survives... for now. 🌱💀🐉")

