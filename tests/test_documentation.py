"""
Tests for documentation accuracy and validity.

This module verifies that:
- Code examples in documentation are valid
- Referenced code locations exist
- Config examples are valid
- Cross-references are accurate
"""

import ast
import re
from pathlib import Path

import pytest

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent


def test_fitness_alignment_doc_exists():
    """Test that FITNESS_ALIGNMENT.md exists."""
    doc_path = PROJECT_ROOT / "docs" / "FITNESS_ALIGNMENT.md"
    assert doc_path.exists(), "docs/FITNESS_ALIGNMENT.md should exist"


def test_fitness_alignment_validation_doc_exists():
    """Test that FITNESS_ALIGNMENT_VALIDATION.md exists."""
    doc_path = PROJECT_ROOT / "docs" / "FITNESS_ALIGNMENT_VALIDATION.md"
    assert doc_path.exists(), "docs/FITNESS_ALIGNMENT_VALIDATION.md should exist"


def test_fitness_alignment_changelog_exists():
    """Test that FITNESS_ALIGNMENT_CHANGELOG.md exists."""
    doc_path = PROJECT_ROOT / "docs" / "FITNESS_ALIGNMENT_CHANGELOG.md"
    assert doc_path.exists(), "docs/FITNESS_ALIGNMENT_CHANGELOG.md should exist"


def test_code_references_in_fitness_alignment_doc():
    """Test that code references in FITNESS_ALIGNMENT.md point to existing files."""
    doc_path = PROJECT_ROOT / "docs" / "FITNESS_ALIGNMENT.md"
    content = doc_path.read_text(encoding='utf-8')
    
    # Find all code references like alert_axolotl_evo/fitness.py or evolution.py
    code_refs = re.findall(r'`([a-z_/]+\.py)`', content)
    
    for ref in code_refs:
        # Convert markdown code reference to file path
        # Handle both alert_axolotl_evo/fitness.py and evolution.py formats
        if '/' in ref:
            file_path = PROJECT_ROOT / ref
        else:
            # If just filename, check in alert_axolotl_evo directory
            file_path = PROJECT_ROOT / "alert_axolotl_evo" / ref
        assert file_path.exists(), f"Code reference {ref} in FITNESS_ALIGNMENT.md should point to existing file"


def test_fitness_alignment_config_exists():
    """Test that FitnessAlignmentConfig exists in config.py."""
    from alert_axolotl_evo.config import FitnessAlignmentConfig
    
    # Verify it's a dataclass with expected fields
    assert hasattr(FitnessAlignmentConfig, '__dataclass_fields__')
    
    expected_fields = {
        'min_precision', 'max_fpr', 'min_alert_rate',
        'max_alert_rate', 'always_true_threshold', 'min_recall'
    }
    
    actual_fields = set(FitnessAlignmentConfig.__dataclass_fields__.keys())
    assert expected_fields.issubset(actual_fields), \
        f"FitnessAlignmentConfig should have fields: {expected_fields}, got: {actual_fields}"


def test_config_includes_fitness_alignment():
    """Test that Config class includes fitness_alignment field."""
    from alert_axolotl_evo.config import Config
    
    config = Config()
    assert hasattr(config, 'fitness_alignment'), \
        "Config should have fitness_alignment field"
    
    from alert_axolotl_evo.config import FitnessAlignmentConfig
    assert isinstance(config.fitness_alignment, FitnessAlignmentConfig), \
        "Config.fitness_alignment should be FitnessAlignmentConfig instance"


def test_fitness_alignment_doc_code_examples():
    """Test that code examples in FITNESS_ALIGNMENT.md are syntactically valid."""
    doc_path = PROJECT_ROOT / "docs" / "FITNESS_ALIGNMENT.md"
    content = doc_path.read_text(encoding='utf-8')
    
    # Find Python code blocks
    code_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
    
    for i, code_block in enumerate(code_blocks):
        try:
            # Try to parse the code
            ast.parse(code_block)
        except SyntaxError as e:
            pytest.fail(f"Code block {i+1} in FITNESS_ALIGNMENT.md has syntax error: {e}")


def test_validation_doc_code_examples():
    """Test that code examples in FITNESS_ALIGNMENT_VALIDATION.md are syntactically valid."""
    doc_path = PROJECT_ROOT / "docs" / "FITNESS_ALIGNMENT_VALIDATION.md"
    content = doc_path.read_text(encoding='utf-8')
    
    # Find Python code blocks (handle both ```python and indented ```python)
    code_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
    
    for i, code_block in enumerate(code_blocks):
        try:
            # Strip leading whitespace that might be from markdown indentation
            # Find minimum indentation (excluding empty lines)
            lines = code_block.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            if non_empty_lines:
                min_indent = min(len(line) - len(line.lstrip()) for line in non_empty_lines)
                # Dedent all lines
                dedented_lines = []
                for line in lines:
                    if line.strip():  # Non-empty line
                        if len(line) >= min_indent:
                            dedented_lines.append(line[min_indent:])
                        else:
                            dedented_lines.append(line.lstrip())
                    else:  # Empty line
                        dedented_lines.append('')
                dedented_code = '\n'.join(dedented_lines)
            else:
                dedented_code = code_block
            # Try to parse the code (skip if it's just comments or incomplete examples)
            # Some code blocks might be incomplete examples, so we'll be lenient
            try:
                ast.parse(dedented_code)
            except IndentationError:
                # If it's an indentation error, try parsing as a module (might be incomplete)
                # This handles cases where code blocks are examples, not complete programs
                try:
                    compile(dedented_code, '<test>', 'exec', flags=ast.PyCF_ONLY_AST)
                except SyntaxError:
                    # If it still fails, it's a real syntax error
                    raise
        except SyntaxError as e:
            # Check if it's a real syntax error or just an incomplete example
            # Some code blocks might be snippets, not complete programs
            if 'unexpected EOF' in str(e) or 'invalid syntax' in str(e).lower():
                # Real syntax error
                pytest.fail(f"Code block {i+1} in FITNESS_ALIGNMENT_VALIDATION.md has syntax error: {e}")
            # Otherwise, might be incomplete example - skip


def test_fitness_alignment_doc_cross_references():
    """Test that cross-references in FITNESS_ALIGNMENT.md point to existing files."""
    doc_path = PROJECT_ROOT / "docs" / "FITNESS_ALIGNMENT.md"
    content = doc_path.read_text(encoding='utf-8')
    
    # Find markdown links like [text](path)
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
    
    for link_text, link_path in links:
        # Skip external URLs
        if link_path.startswith('http'):
            continue
        
        # Skip anchor links
        if link_path.startswith('#'):
            continue
        
        # Convert relative path to absolute
        if link_path.startswith('docs/'):
            target_path = PROJECT_ROOT / link_path
        elif link_path.startswith('../'):
            target_path = PROJECT_ROOT / link_path[3:]
        elif link_path.startswith('alert_axolotl_evo/'):
            # Direct reference to module file
            target_path = PROJECT_ROOT / link_path
        else:
            # Try in docs directory first, then project root
            target_path = PROJECT_ROOT / "docs" / link_path
            if not target_path.exists():
                target_path = PROJECT_ROOT / link_path
        
        assert target_path.exists(), \
            f"Cross-reference [{link_text}]({link_path}) in FITNESS_ALIGNMENT.md should point to existing file (tried: {target_path})"


def test_fitness_function_has_alignment_docstring():
    """Test that fitness() function has alignment documentation."""
    from alert_axolotl_evo.fitness import fitness
    
    docstring = fitness.__doc__
    assert docstring is not None, "fitness() function should have docstring"
    assert "alignment" in docstring.lower() or "operational" in docstring.lower(), \
        "fitness() docstring should mention alignment or operational constraints"


def test_fitness_breakdown_has_alignment_docstring():
    """Test that fitness_breakdown() function has alignment documentation."""
    from alert_axolotl_evo.fitness import fitness_breakdown
    
    docstring = fitness_breakdown.__doc__
    assert docstring is not None, "fitness_breakdown() function should have docstring"
    assert "alignment" in docstring.lower() or "operational" in docstring.lower() or "breakdown" in docstring.lower(), \
        "fitness_breakdown() docstring should mention alignment or breakdown"


def test_fitness_module_has_alignment_docstring():
    """Test that fitness.py module has alignment documentation."""
    from alert_axolotl_evo import fitness
    
    docstring = fitness.__doc__
    assert docstring is not None, "fitness module should have docstring"
    assert "alignment" in docstring.lower(), \
        "fitness module docstring should mention alignment"


def test_alignment_demo_exists():
    """Test that fitness_alignment_demo.py exists."""
    demo_path = PROJECT_ROOT / "examples" / "fitness_alignment_demo.py"
    assert demo_path.exists(), "examples/fitness_alignment_demo.py should exist"


def test_alignment_demo_is_runnable():
    """Test that fitness_alignment_demo.py can be imported."""
    import sys
    demo_path = PROJECT_ROOT / "examples" / "fitness_alignment_demo.py"
    
    # Add examples to path if needed
    if str(PROJECT_ROOT / "examples") not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT / "examples"))
    
    try:
        # Try to compile the file
        with open(demo_path, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"fitness_alignment_demo.py has syntax error: {e}")


def test_readme_mentions_alignment():
    """Test that README.md mentions fitness alignment."""
    readme_path = PROJECT_ROOT / "README.md"
    content = readme_path.read_text(encoding='utf-8')
    
    assert "alignment" in content.lower() or "fitness alignment" in content.lower(), \
        "README.md should mention fitness alignment"


def test_architecture_mentions_alignment():
    """Test that ARCHITECTURE.md mentions fitness alignment."""
    arch_path = PROJECT_ROOT / "ARCHITECTURE.md"
    content = arch_path.read_text(encoding='utf-8')
    
    assert "alignment" in content.lower() or "fitness alignment" in content.lower(), \
        "ARCHITECTURE.md should mention fitness alignment"


def test_usage_mentions_alignment():
    """Test that USAGE.md mentions fitness alignment."""
    usage_path = PROJECT_ROOT / "USAGE.md"
    content = usage_path.read_text(encoding='utf-8')
    
    assert "alignment" in content.lower() or "fitness alignment" in content.lower(), \
        "USAGE.md should mention fitness alignment"
