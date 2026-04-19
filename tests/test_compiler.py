"""Tests for compiler module."""


from alert_axolotl_evo.compiler import PrimitiveCompiler
from alert_axolotl_evo.fitness import evaluate


class TestPrimitiveCompiler:
    """Test PrimitiveCompiler class."""
    
    def test_init(self):
        """Test compiler initialization."""
        compiler = PrimitiveCompiler(evaluate)
        assert compiler.evaluate == evaluate
    
    def test_compile_macro_creates_closure(self):
        """Test that compile_macro creates a callable closure."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (">", ("avg", "latency"), 100)
        
        macro = compiler.compile_macro(subtree)
        assert callable(macro)
        assert hasattr(macro, 'needs_context')
        assert hasattr(macro, 'subtree_definition')
    
    def test_compile_macro_metadata_needs_context(self):
        """Test that compiled macro has needs_context=True."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (">", ("avg", "latency"), 100)
        
        macro = compiler.compile_macro(subtree)
        assert macro.needs_context is True
    
    def test_compile_macro_metadata_subtree_definition(self):
        """Test that compiled macro has subtree_definition attached."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (">", ("avg", "latency"), 100)
        
        macro = compiler.compile_macro(subtree)
        assert hasattr(macro, 'subtree_definition')
        assert macro.subtree_definition == subtree
    
    def test_compile_macro_execution_with_context(self):
        """Test that compiled macro executes correctly with data context."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (">", ("avg", "latency"), 100)
        
        macro = compiler.compile_macro(subtree)
        
        # Test with data that should return True
        data = {"latency": [150, 160, 170]}
        result = macro(data)
        assert result is True
        
        # Test with data that should return False
        data2 = {"latency": [50, 60, 70]}
        result2 = macro(data2)
        assert result2 is False
    
    def test_compile_macro_execution_with_empty_args(self):
        """Test that macro accepts empty *args (0-arity)."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (">", ("avg", "latency"), 100)
        
        macro = compiler.compile_macro(subtree)
        
        # Should work with no extra args
        data = {"latency": [150]}
        result = macro(data)
        assert isinstance(result, bool)
        
        # Should also work with empty *args
        result2 = macro(data, *[])
        assert isinstance(result2, bool)
    
    def test_compile_macro_introspection(self):
        """Test that subtree_definition can be accessed for introspection."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = ("and", (">", ("avg", "latency"), 100), ("<", ("max", "latency"), 200))
        
        macro = compiler.compile_macro(subtree)
        
        # Should be able to access the original subtree
        introspected = macro.subtree_definition
        assert introspected == subtree
        assert isinstance(introspected, tuple)
        assert len(introspected) == 3
    
    def test_compile_macro_different_subtrees(self):
        """Test that different subtrees produce different macros."""
        compiler = PrimitiveCompiler(evaluate)
        subtree1 = (">", ("avg", "latency"), 100)
        subtree2 = ("<", ("max", "latency"), 200)
        
        macro1 = compiler.compile_macro(subtree1)
        macro2 = compiler.compile_macro(subtree2)
        
        # They should have different subtree definitions
        assert macro1.subtree_definition != macro2.subtree_definition
        
        # They should both have needs_context
        assert macro1.needs_context is True
        assert macro2.needs_context is True
    
    def test_compile_macro_complex_subtree(self):
        """Test compiling a complex nested subtree."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (
            "if_alert",
            ("and",
                (">", ("avg", "latency"), 100),
                ("<", ("max", "latency"), 200)
            ),
            "Complex alert!"
        )
        
        macro = compiler.compile_macro(subtree)
        assert macro.subtree_definition == subtree
        
        # Test execution
        data = {"latency": [150, 160, 170]}
        result = macro(data)
        assert result == "Complex alert!"
    
    def test_compile_macro_error_handling(self):
        """Test that macro handles evaluation errors gracefully."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (">", ("avg", "latency"), 100)
        
        macro = compiler.compile_macro(subtree)
        
        # Test with invalid data (should not crash)
        data = {"latency": None}
        result = macro(data)
        # Should return None or handle gracefully
        assert result is None or isinstance(result, (bool, type(None)))
    
    def test_compile_macro_preserves_subtree_structure(self):
        """Test that subtree structure is preserved exactly."""
        compiler = PrimitiveCompiler(evaluate)
        original_subtree = (">", ("avg", "latency"), 100)
        
        macro = compiler.compile_macro(original_subtree)
        
        # The subtree_definition should be identical
        preserved = macro.subtree_definition
        assert preserved == original_subtree
        # Note: Python may reuse tuple objects, so we just check equality
        assert isinstance(preserved, tuple)
        assert len(preserved) == 3
    
    def test_compile_macro_with_nested_macros(self):
        """Test that macro can contain nested function calls."""
        compiler = PrimitiveCompiler(evaluate)
        subtree = (
            "and",
            (">", ("avg", "latency"), 100),
            ("<", ("percentile", "latency", 90), 200)
        )
        
        macro = compiler.compile_macro(subtree)
        assert macro.subtree_definition == subtree
        
        # Test execution
        data = {"latency": [110, 120, 130, 140, 150]}
        result = macro(data)
        assert isinstance(result, bool)
