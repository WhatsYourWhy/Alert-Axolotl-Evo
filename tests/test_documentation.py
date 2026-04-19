"""Sanity checks for documentation: code refs resolve, code blocks parse."""

import ast
import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
DOCS = PROJECT_ROOT / "docs"
FITNESS_DOC = DOCS / "fitness-alignment.md"


def test_fitness_alignment_doc_exists():
    assert FITNESS_DOC.exists()


def test_fitness_alignment_doc_code_examples_parse():
    content = FITNESS_DOC.read_text(encoding="utf-8")
    for i, block in enumerate(re.findall(r"```python\n(.*?)\n```", content, re.DOTALL)):
        try:
            ast.parse(block)
        except SyntaxError as e:
            pytest.fail(f"fitness-alignment.md block {i+1} has syntax error: {e}")


def test_fitness_alignment_doc_code_references_exist():
    content = FITNESS_DOC.read_text(encoding="utf-8")
    for ref in re.findall(r"`([a-z_/]+\.py)`", content):
        target = PROJECT_ROOT / ref if "/" in ref else PROJECT_ROOT / "alert_axolotl_evo" / ref
        assert target.exists(), f"Stale code reference in fitness-alignment.md: {ref}"


def test_fitness_alignment_config_exists():
    from alert_axolotl_evo.config import FitnessAlignmentConfig

    expected = {
        "min_precision", "max_fpr", "min_alert_rate",
        "max_alert_rate", "always_true_threshold", "min_recall",
    }
    actual = set(FitnessAlignmentConfig.__dataclass_fields__.keys())
    assert expected.issubset(actual)


def test_config_includes_fitness_alignment():
    from alert_axolotl_evo.config import Config, FitnessAlignmentConfig

    assert isinstance(Config().fitness_alignment, FitnessAlignmentConfig)


def test_fitness_module_has_alignment_docstring():
    from alert_axolotl_evo import fitness

    assert fitness.__doc__ and "alignment" in fitness.__doc__.lower()


def test_readme_mentions_alignment():
    content = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert "alignment" in content.lower()


def test_alignment_demo_parses():
    demo = PROJECT_ROOT / "examples" / "fitness_alignment_demo.py"
    assert demo.exists()
    ast.parse(demo.read_text(encoding="utf-8"))
