"""Tree manipulation utilities."""

import hashlib
from typing import Any, List, Tuple


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


def is_valid_subtree(tree: Any, arities: dict) -> bool:
    """Check if a subtree is valid according to arities."""
    if not isinstance(tree, tuple):
        return True
    if not tree:
        return False
    op = tree[0]
    if op not in arities:
        return False
    if len(tree) - 1 != arities[op]:
        return False
    return all(is_valid_subtree(child, arities) for child in tree[1:])

