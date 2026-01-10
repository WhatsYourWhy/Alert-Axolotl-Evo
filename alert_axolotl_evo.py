"""Alert Axolotl Evo: a deterministic, gamified genetic programming system."""

import hashlib
import logging
import random
from typing import Any, Dict, Iterable, List, Sequence, Tuple


# ----------------------------
# Primitive definitions
# ----------------------------
FUNCTIONS = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    "and": lambda a, b: a and b,
    "or": lambda a, b: a or b,
    "avg": lambda vals: sum(vals) / len(vals) if vals else 0,
}
ALERT = lambda cond, msg: msg if cond else None
TERMINALS: List[Any] = ["latency", 50, 100, "High alert!", "Danger zone!"]


# ----------------------------
# Tree utilities
# ----------------------------
def tree_hash(tree: Any) -> str:
    """Short deterministic hash for a tree."""
    digest = hashlib.sha256(str(tree).encode("utf-8")).hexdigest()
    return digest[:6]


def node_count(tree: Any) -> int:
    """Count nodes for parsimony and bloat control."""
    if not isinstance(tree, tuple):
        return 1
    return 1 + sum(node_count(child) for child in tree[1:])


def get_subtree_paths(tree: Any, path: Tuple[int, ...] = ()) -> List[Tuple[Tuple[int, ...], Any]]:
    """Collect subtree paths for crossover and mutation."""
    paths = [(path, tree)]
    if isinstance(tree, tuple):
        for idx, child in enumerate(tree[1:], start=1):
            paths.extend(get_subtree_paths(child, path + (idx,)))
    return paths


def replace_subtree(tree: Any, path: Tuple[int, ...], new_subtree: Any) -> Any:
    """Replace subtree at path with new_subtree."""
    if not path:
        return new_subtree
    if not isinstance(tree, tuple):
        return tree
    index = path[0]
    children = list(tree[1:])
    child_index = index - 1
    children[child_index] = replace_subtree(children[child_index], path[1:], new_subtree)
    return (tree[0], *children)


# ----------------------------
# Tree generation
# ----------------------------
def random_terminal() -> Any:
    return random.choice(TERMINALS)


def random_function() -> str:
    return random.choice(["if_alert", ">", "<", "and", "or", "avg"])


def grow_tree(depth: int, max_depth: int) -> Any:
    """Grow method: choose function or terminal stochastically."""
    if depth >= max_depth or (depth > 0 and random.random() < 0.5):
        return random_terminal()
    func = random_function()
    if func == "avg":
        return (func, grow_tree(depth + 1, max_depth))
    if func == "if_alert":
        return (func, grow_tree(depth + 1, max_depth), random_terminal())
    return (func, grow_tree(depth + 1, max_depth), grow_tree(depth + 1, max_depth))


def full_tree(depth: int, max_depth: int) -> Any:
    """Full method: always expand until max_depth."""
    if depth >= max_depth:
        return random_terminal()
    func = random_function()
    if func == "avg":
        return (func, full_tree(depth + 1, max_depth))
    if func == "if_alert":
        return (func, full_tree(depth + 1, max_depth), random_terminal())
    return (func, full_tree(depth + 1, max_depth), full_tree(depth + 1, max_depth))


def initialize_population(pop_size: int, min_depth: int, max_depth: int) -> List[Any]:
    """Koza ramped half-and-half initialization."""
    population: List[Any] = []
    depths = list(range(min_depth, max_depth + 1))
    while len(population) < pop_size:
        for depth in depths:
            if len(population) >= pop_size:
                break
            if len(population) % 2 == 0:
                population.append(grow_tree(0, depth))
            else:
                population.append(full_tree(0, depth))
    return population


# ----------------------------
# Evaluation and display
# ----------------------------
def coerce_number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):
        return FUNCTIONS["avg"](value)
    return 0.0


def evaluate(tree: Any, data: Dict[str, Any]) -> Any:
    """Recursively evaluate a tree."""
    if isinstance(tree, tuple):
        op = tree[0]
        if op == "if_alert":
            cond = evaluate(tree[1], data)
            msg = evaluate(tree[2], data)
            return ALERT(bool(cond), msg)
        if op == "avg":
            vals = evaluate(tree[1], data)
            if not isinstance(vals, list):
                vals = [coerce_number(vals)]
            return FUNCTIONS[op](vals)
        left = evaluate(tree[1], data)
        right = evaluate(tree[2], data)
        if op in (">", "<"):
            return FUNCTIONS[op](coerce_number(left), coerce_number(right))
        if op in ("and", "or"):
            return FUNCTIONS[op](bool(left), bool(right))
    if isinstance(tree, str) and tree in data:
        return data[tree]
    return tree


def print_ascii_tree(tree: Any, prefix: str = "", is_last: bool = True) -> str:
    """Render a tree with box-drawing characters."""
    connector = "└─ " if is_last else "├─ "
    lines = [f"{prefix}{connector}{tree[0]}" if isinstance(tree, tuple) else f"{prefix}{connector}{tree}"]
    if isinstance(tree, tuple):
        child_prefix = f"{prefix}{'   ' if is_last else '│  '}"
        children = list(tree[1:])
        for idx, child in enumerate(children):
            lines.append(print_ascii_tree(child, child_prefix, idx == len(children) - 1))
    return "\n".join(lines)


def generate_name(tree: Any) -> str:
    """Generate a fun, deterministic name based on tree structure."""
    tree_str = str(tree)
    gt_count = tree_str.count("'>'")
    avg_count = tree_str.count("'avg'")
    and_count = tree_str.count("'and'")
    if gt_count >= 3:
        return "Spikezilla the Threshold Tyrant"
    if avg_count >= 3:
        return "Smoothie the Eternal Averager"
    if and_count >= 3:
        return "Bloaty McRedundantface"
    choices = [
        "Guardian Gremlin",
        "Chaos Critter",
        "Alert Axolotl",
        "Siren Salamander",
        "Whispering Watcher",
    ]
    seed = int(hashlib.sha256(tree_str.encode("utf-8")).hexdigest(), 16)
    rng = random.Random(seed)
    return rng.choice(choices)


# ----------------------------
# Fitness and evolution
# ----------------------------
def generate_mock_data(seed: int, size: int = 100) -> Tuple[List[float], List[bool]]:
    """Generate deterministic mock latency data with anomalies."""
    rng = random.Random(seed)
    values = [rng.gauss(50, 10) for _ in range(size)]
    anomaly_idx = set(rng.sample(range(size), 8))
    anomalies = []
    for idx, value in enumerate(values):
        if idx in anomaly_idx:
            values[idx] = value * 2.5
            anomalies.append(True)
        else:
            anomalies.append(False)
    return values, anomalies


def fitness(tree: Any, seed: int, gen: int) -> float:
    """Compute fitness based on detection quality and parsimony."""
    values, anomalies = generate_mock_data(seed + gen)
    tp = fp = 0
    for idx, value in enumerate(values):
        window_size = 5 + (idx % 2)
        start = max(0, idx - window_size + 1)
        window = values[start : idx + 1]
        data = {"latency": window}
        result = evaluate(tree, data)
        alerting = result is not None
        if anomalies[idx] and alerting:
            tp += 1
        if not anomalies[idx] and alerting:
            fp += 1
    penalty = 0.005 * len(str(tree))
    return tp - 2 * fp - penalty


def tournament_select(scored: List[Tuple[Any, float]], size: int = 4) -> Any:
    """Tournament selection."""
    contenders = random.sample(scored, size)
    contenders.sort(key=lambda item: (-item[1], node_count(item[0])))
    return contenders[0][0]


def subtree_crossover(parent_a: Any, parent_b: Any) -> Tuple[Any, Any]:
    """Swap random subtrees between two parents."""
    paths_a = get_subtree_paths(parent_a)
    paths_b = get_subtree_paths(parent_b)
    path_a, subtree_a = random.choice(paths_a)
    path_b, subtree_b = random.choice(paths_b)
    child_a = replace_subtree(parent_a, path_a, subtree_b)
    child_b = replace_subtree(parent_b, path_b, subtree_a)
    return child_a, child_b


def point_mutation(tree: Any, max_depth: int = 2) -> Any:
    """Replace a random subtree with a new random grow tree."""
    paths = get_subtree_paths(tree)
    path, _ = random.choice(paths)
    new_subtree = grow_tree(0, max_depth)
    return replace_subtree(tree, path, new_subtree)


def log_funeral(tree: Any, gen: int) -> None:
    """Print a dramatic funeral for culled individuals."""
    name = generate_name(tree)
    cause = random.choice(["terminal bloat", "false-alarm fever", "overfitted hubris", "anomaly blindness"])
    last_words = str(tree)[:60] + ("..." if len(str(tree)) > 60 else "")
    logger = logging.getLogger("evo")
    logger.info("RIP %s (hash:%s) [gen %s]", name, tree_hash(tree), gen)
    logger.info("Cause of demise: %s", cause)
    logger.info("Last words: %s", last_words)
    logger.info("Trash-talk: 'Maybe try being useful next time.'")


def announce_birth(tree: Any) -> None:
    name = generate_name(tree)
    logging.getLogger("evo").info("A new beast awakens: %s (hash:%s)", name, tree_hash(tree))


def evolve(seed: int = 42, pop_size: int = 50, generations: int = 40) -> None:
    """Main evolution loop."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    random.seed(seed)

    population = initialize_population(pop_size, 2, 7)
    for tree in population:
        announce_birth(tree)

    for gen in range(generations):
        logging.getLogger("evo").info("\n=== Generation %s ===", gen)
        scored = []
        for tree in population:
            fit = fitness(tree, seed, gen)
            name = generate_name(tree)
            logging.getLogger("evo").info("%s faces the anomaly horde... fitness %.2f", name, fit)
            scored.append((tree, fit))

        scored.sort(key=lambda item: (-item[1], node_count(item[0])))
        champion, champ_fit = scored[0]
        logging.getLogger("evo").info("→ 🐉 ROARS VICTORIOUSLY!")
        print(print_ascii_tree(champion))
        if champ_fit > 0.9:
            logging.getLogger("evo").info("💥⚡🌟🔥 *CRASH* Anomaly detected! 🌟🔥⚡💥")

        elites_count = max(1, int(0.1 * pop_size))
        elites = [tree for tree, _ in scored[:elites_count]]
        for tree, _ in scored[elites_count:]:
            log_funeral(tree, gen)

        next_population = elites[:]
        while len(next_population) < pop_size:
            parent_a = tournament_select(scored)
            parent_b = tournament_select(scored)
            if random.random() < 0.9:
                child_a, child_b = subtree_crossover(parent_a, parent_b)
            else:
                child_a, child_b = parent_a, parent_b
            if random.random() < 0.2:
                child_a = point_mutation(child_a)
            if random.random() < 0.2:
                child_b = point_mutation(child_b)
            next_population.extend([child_a, child_b])

        population = next_population[:pop_size]
        for tree in population:
            announce_birth(tree)

    logging.getLogger("evo").info("Evolution complete. The fittest guardian survives... for now. 🌱💀🐉")


if __name__ == "__main__":
    evolve(seed=42)
