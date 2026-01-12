"""Tree manipulation utilities."""

import hashlib
import random
from typing import Any, List, Optional, Set, Tuple, Union

from alert_axolotl_evo.primitives import ARITIES, MSG_TERMINALS


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


def is_boolean_expression(tree: Any, arities: dict) -> bool:
    """
    Check if a subtree is a boolean-returning expression.
    
    A boolean expression is:
    - A comparison operator (>, <, >=, <=, ==, !=)
    - A logical operator (and, or, not)
    - NOT a terminal (string, number, or variable name)
    - NOT a statistical function (avg, max, min, etc.)
    """
    if not isinstance(tree, tuple):
        return False  # Terminals are not boolean expressions
    if not tree:
        return False
    op = tree[0]
    # Boolean-returning functions
    boolean_ops = [">", "<", ">=", "<=", "==", "!=", "and", "or", "not"]
    if op in boolean_ops:
        # Check that children are valid subtrees
        if op not in arities:
            return False
        if len(tree) - 1 != arities[op]:
            return False
        
        # For logical operators (and, or, not), children must also be boolean expressions
        # This prevents strings/numbers from being used directly in boolean ops
        if op in ("and", "or", "not"):
            if op == "not":
                return is_boolean_expression(tree[1], arities)
            else:
                return (is_boolean_expression(tree[1], arities) and 
                        is_boolean_expression(tree[2], arities))
        
        # For comparison operators, children can be numeric expressions (statistical functions, numbers, variables)
        # But not message terminals or boolean expressions (comparisons produce booleans, not consume them)
        for child in tree[1:]:
            if isinstance(child, str) and child in MSG_TERMINALS:
                return False  # Message terminal in comparison - invalid
            # Allow numeric terminals, variables, and statistical functions
            if isinstance(child, (int, float)):
                continue  # Numeric literal - OK
            if isinstance(child, str) and child == "latency":
                continue  # Variable name - OK
            if isinstance(child, tuple):
                # Statistical function - OK (e.g., ('avg', 'latency'))
                if child[0] in ("avg", "max", "min", "sum", "count", "stddev", "percentile", 
                                "window_avg", "window_max", "window_min"):
                    if is_valid_subtree(child, arities):
                        continue
            # Anything else (including other terminals) is invalid
            return False
        return True
    # Statistical functions can be used in comparisons, but aren't boolean themselves
    # They need to be wrapped in a comparison
    return False


def is_valid_alert_rule(tree: Any) -> bool:
    """
    Check if a tree is a semantically valid alert rule.
    
    A valid alert rule must:
    - Be a tuple (not a terminal)
    - Have "if_alert" at root
    - Have correct arity (2 arguments: condition and message)
    - Condition must be a boolean-returning expression (not a message terminal)
    - Message must be a message terminal (string from MSG_TERMINALS)
    - All children must be valid subtrees according to arities
    
    Args:
        tree: Tree structure to validate
        
    Returns:
        True if tree is a valid alert rule, False otherwise
    """
    if not isinstance(tree, tuple):
        return False
    if not tree:
        return False
    if tree[0] != "if_alert":
        return False
    if len(tree) != 3:  # if_alert requires 2 arguments
        return False
    
    condition_subtree = tree[1]
    message_terminal = tree[2]
    
    # Condition must be a boolean-returning expression
    # This prevents message terminals from being used as conditions
    if not is_boolean_expression(condition_subtree, ARITIES):
        return False  # Condition is not a valid boolean expression
    
    # Message must be a string terminal (preferably from MSG_TERMINALS)
    if not isinstance(message_terminal, str):
        return False
    
    # Recursively validate children structure
    return is_valid_subtree(tree, ARITIES)


def ensure_alert_root(tree: Any, rng: Optional[random.Random] = None) -> Any:
    """
    Ensure tree has if_alert at root, wrapping if necessary.
    
    If tree already has if_alert at root, returns as-is.
    Otherwise, wraps tree: ("if_alert", tree, random_message)
    
    Args:
        tree: Tree structure to repair
        rng: Optional random number generator (for determinism)
            If None, uses module-level random (less deterministic but backward compatible)
        
    Returns:
        Tree with if_alert at root
    """
    if is_valid_alert_rule(tree):
        return tree
    
    # Use provided RNG or module-level random (for backward compatibility)
    # Note: For full determinism, callers should pass seeded RNG
    if rng is not None:
        message = rng.choice(MSG_TERMINALS)
    else:
        message = random.choice(MSG_TERMINALS)
    
    # Wrap tree with if_alert
    return ("if_alert", tree, message)

