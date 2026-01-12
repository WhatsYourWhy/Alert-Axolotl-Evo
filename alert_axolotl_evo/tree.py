"""Tree manipulation utilities."""

import hashlib
from typing import Any, List, Optional, Set, Tuple, Union


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


def get_stable_hash(content: str) -> str:
    """Generate a deterministic SHA-256 hash for a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def normalize_tree_structure(node: Any) -> Any:
    """
    Convert lists to tuples for consistent hashing across JSON loads.
    
    Args:
        node: Tree structure (tuple, list, or terminal)
        
    Returns:
        Normalized structure (tuples instead of lists)
    """
    if isinstance(node, list):
        return tuple(normalize_tree_structure(child) for child in node)
    if isinstance(node, tuple):
        return tuple(normalize_tree_structure(child) for child in node)
    return node


def merkle_hash(
    node: Union[Tuple, list, str, int, float],
    normalize_vars: bool = False,
    alert_messages: Optional[Set[str]] = None
) -> str:
    """
    Compute a structural hash of the tree/subtree using Merkle hashing.
    
    Each node's hash includes its own value and the hashes of its children.
    This produces identical hashes for structurally identical subtrees.
    
    Args:
        node: The tree node (tuple, list, or terminal)
        normalize_vars: If True, treats variable names as '__VAR__' 
                       to find structural matches regardless of specific metrics
        alert_messages: Set of known alert message strings (to avoid normalizing them)
        
    Returns:
        16-character hex hash string
    """
    # Normalize structure first (lists -> tuples)
    node = normalize_tree_structure(node)
    
    # Terminal node
    if not isinstance(node, tuple):
        if normalize_vars and isinstance(node, str):
            # Don't normalize if it's a known alert message
            if alert_messages and node in alert_messages:
                return get_stable_hash(str(node))
            
            # Heuristic: short identifiers without spaces/punctuation are variables
            # Alert messages are typically longer and contain punctuation
            if len(node) < 30 and not any(c in node for c in [' ', '!', '?', '.']):
                return get_stable_hash("__VAR__")
        
        # Numeric constants and alert messages: keep exact
        value_str = str(node)
        type_str = type(node).__name__
        content = f"TERMINAL:{type_str}:{value_str}"
        return get_stable_hash(content)
    
    # Function node - function name is NEVER normalized
    if not node:
        return get_stable_hash("EMPTY")
    
    func_name = node[0]
    
    # Recursively hash children
    child_hashes = [
        merkle_hash(child, normalize_vars, alert_messages) 
        for child in node[1:]
    ]
    
    # Combine function name + child hashes
    # Structure: func_name + child1_hash + child2_hash...
    combined_content = f"FUNC:{func_name}:" + "".join(child_hashes)
    
    return get_stable_hash(combined_content)

