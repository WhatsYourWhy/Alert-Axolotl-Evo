"""Visualization and gamified narrative functions."""

import hashlib
import logging
import random
from typing import Any

from alert_axolotl_evo.tree import tree_hash


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
    """Announce the birth of a new individual."""
    name = generate_name(tree)
    logging.getLogger("evo").info("A new beast awakens: %s (hash:%s)", name, tree_hash(tree))

