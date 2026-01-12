"""
Compiler module: Converts evolved subtrees into registered 0-arity functions.
Architectural Decision: 'Macros' are registered as functions with arity=0, not terminals.
"""
from typing import Any, Callable, Dict, Tuple


class PrimitiveCompiler:
    def __init__(self, evaluate_fn: Callable):
        """
        Args:
            evaluate_fn: The core evaluate(tree, data) function.
                         Signature: evaluate(tree: Tuple, data: Dict[str, Any]) -> Any
        """
        self.evaluate = evaluate_fn

    def compile_macro(self, subtree: Tuple) -> Callable:
        """
        Compiles an EXACT subtree into a 0-arity function closure.
        
        The resulting function is tagged with needs_context=True so the
        evaluator knows to inject the data dict as the first argument.
        
        Args:
            subtree: The exact tree structure to compile (tuple representation)
            
        Returns:
            A closure that executes the subtree against the current context.
            The function has metadata attached:
            - needs_context: True (for evaluator)
            - subtree_definition: The original subtree (for introspection)
        """
        # Closure captures the subtree structure
        def macro_impl(data: Dict[str, Any], *args):
            # For 0-arity macros, *args should be empty
            # But we accept them to be safe (future: variadic macros?)
            return self.evaluate(subtree, data)
        
        # 1. Metadata for Evaluator (Runtime)
        macro_impl.needs_context = True
        
        # 2. Metadata for Promotion Manager (Introspection)
        # CRITICAL: This is the Source of Truth for what this macro actually does.
        # Only macros have this attribute - it's the "macro marker"
        macro_impl.subtree_definition = subtree
        
        return macro_impl
