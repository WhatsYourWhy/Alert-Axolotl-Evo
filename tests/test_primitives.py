"""Tests for primitives module."""


from alert_axolotl_evo.primitives import (
    ARITIES,
    FUNCTION_NAMES,
    FUNCTIONS,
    TERMINALS,
    register_function,
    register_terminal,
    unregister_function,
)


class TestRegisterFunction:
    """Test register_function."""
    
    def test_register_function_basic(self):
        """Test basic function registration."""
        def test_func(a, b):
            return a + b
        
        register_function("test_add", test_func, arity=2)
        
        assert "test_add" in FUNCTIONS
        assert FUNCTIONS["test_add"] == test_func
        assert ARITIES["test_add"] == 2
        assert "test_add" in FUNCTION_NAMES
    
    def test_register_function_needs_context(self):
        """Test registration with needs_context=True."""
        def test_macro(data, *args):
            return data.get("value", 0)
        
        register_function("test_macro", test_macro, arity=0, needs_context=True)
        
        assert "test_macro" in FUNCTIONS
        assert hasattr(test_macro, "needs_context")
        assert test_macro.needs_context is True
    
    def test_register_function_determinism(self):
        """Test that FUNCTION_NAMES remains sorted after registration."""
        initial_names = FUNCTION_NAMES.copy()
        
        register_function("zzz_last", lambda x: x, arity=1)
        register_function("aaa_first", lambda x: x, arity=1)
        
        # Should be sorted
        assert FUNCTION_NAMES == sorted(FUNCTION_NAMES)
        assert "aaa_first" in FUNCTION_NAMES
        assert "zzz_last" in FUNCTION_NAMES
        
        # Cleanup
        unregister_function("zzz_last")
        unregister_function("aaa_first")
    
    def test_register_function_duplicate_name(self):
        """Test that duplicate names don't create duplicates in FUNCTION_NAMES."""
        def func1(x):
            return x
        
        def func2(x):
            return x * 2
        
        register_function("duplicate_test", func1, arity=1)
        count_before = FUNCTION_NAMES.count("duplicate_test")
        
        register_function("duplicate_test", func2, arity=1)
        count_after = FUNCTION_NAMES.count("duplicate_test")
        
        # Should still be only one entry
        assert count_after == 1
        assert FUNCTIONS["duplicate_test"] == func2  # Latest wins
        
        # Cleanup
        unregister_function("duplicate_test")
    
    def test_register_function_backward_compatibility(self):
        """Test that existing registrations still work without needs_context."""
        def standard_func(a, b):
            return a * b
        
        register_function("test_mult", standard_func, arity=2)
        
        assert "test_mult" in FUNCTIONS
        assert not hasattr(standard_func, "needs_context")
        
        # Cleanup
        unregister_function("test_mult")


class TestUnregisterFunction:
    """Test unregister_function."""
    
    def test_unregister_function_basic(self):
        """Test basic function unregistration."""
        def test_func(x):
            return x
        
        register_function("test_unreg", test_func, arity=1)
        assert "test_unreg" in FUNCTIONS
        
        unregister_function("test_unreg")
        
        assert "test_unreg" not in FUNCTIONS
        assert "test_unreg" not in ARITIES
        assert "test_unreg" not in FUNCTION_NAMES
    
    def test_unregister_function_nonexistent(self):
        """Test that unregistering nonexistent function doesn't crash."""
        # Should not raise
        unregister_function("nonexistent_function")
    
    def test_unregister_function_preserves_others(self):
        """Test that unregistering one function doesn't affect others."""
        def func1(x):
            return x
        
        def func2(x):
            return x * 2
        
        register_function("test_func1", func1, arity=1)
        register_function("test_func2", func2, arity=1)
        
        assert "test_func1" in FUNCTIONS
        assert "test_func2" in FUNCTIONS
        
        unregister_function("test_func1")
        
        assert "test_func1" not in FUNCTIONS
        assert "test_func2" in FUNCTIONS  # Still there
        
        # Cleanup
        unregister_function("test_func2")
    
    def test_unregister_function_with_needs_context(self):
        """Test unregistering a function with needs_context."""
        def test_macro(data, *args):
            return data.get("value", 0)
        
        register_function("test_macro_unreg", test_macro, arity=0, needs_context=True)
        assert "test_macro_unreg" in FUNCTIONS
        
        unregister_function("test_macro_unreg")
        
        assert "test_macro_unreg" not in FUNCTIONS
        assert "test_macro_unreg" not in ARITIES
        assert "test_macro_unreg" not in FUNCTION_NAMES


class TestRegisterTerminal:
    """Test register_terminal."""
    
    def test_register_terminal_basic(self):
        """Test basic terminal registration."""
        register_terminal(300)
        
        assert 300 in TERMINALS
    
    def test_register_terminal_duplicate(self):
        """Test that duplicate terminals are not added."""
        initial_count = len(TERMINALS)
        
        register_terminal(999)
        count_after_first = len(TERMINALS)
        
        register_terminal(999)  # Duplicate
        count_after_second = len(TERMINALS)
        
        assert count_after_first == initial_count + 1
        assert count_after_second == count_after_first  # No duplicate
        
        # Cleanup
        if 999 in TERMINALS:
            TERMINALS.remove(999)


class TestPrimitivesIntegration:
    """Integration tests for primitives."""
    
    def test_register_unregister_cycle(self):
        """Test complete register/unregister cycle."""
        def test_func(x):
            return x + 1
        
        # Register
        register_function("cycle_test", test_func, arity=1)
        assert "cycle_test" in FUNCTIONS
        assert "cycle_test" in FUNCTION_NAMES
        
        # Unregister
        unregister_function("cycle_test")
        assert "cycle_test" not in FUNCTIONS
        assert "cycle_test" not in FUNCTION_NAMES
        
        # Re-register should work
        register_function("cycle_test", test_func, arity=1)
        assert "cycle_test" in FUNCTIONS
        
        # Cleanup
        unregister_function("cycle_test")
    
    def test_macro_registration_workflow(self):
        """Test complete workflow for registering a macro."""
        def macro_func(data, *args):
            return data.get("value", 0) > 100
        
        # Register as macro
        register_function("test_macro_workflow", macro_func, arity=0, needs_context=True)
        
        assert "test_macro_workflow" in FUNCTIONS
        assert macro_func.needs_context is True
        assert ARITIES["test_macro_workflow"] == 0
        
        # Unregister
        unregister_function("test_macro_workflow")
        assert "test_macro_workflow" not in FUNCTIONS
    
    def test_determinism_after_multiple_registrations(self):
        """Test that FUNCTION_NAMES remains sorted after multiple registrations."""
        functions_to_add = ["z_func", "a_func", "m_func", "b_func"]
        
        for name in functions_to_add:
            register_function(name, lambda x: x, arity=1)
        
        # Should be sorted
        assert FUNCTION_NAMES == sorted(FUNCTION_NAMES)
        
        # All should be present
        for name in functions_to_add:
            assert name in FUNCTION_NAMES
        
        # Cleanup
        for name in functions_to_add:
            unregister_function(name)
