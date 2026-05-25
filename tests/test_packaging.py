"""Packaging regression tests."""

import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_built_wheel_includes_fitness_subpackage(tmp_path):
    """The public fitness package must be present in built distributions."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir",
            str(tmp_path),
            str(PROJECT_ROOT),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    wheels = list(tmp_path.glob("alert_axolotl_evo-*.whl"))
    assert len(wheels) == 1

    with zipfile.ZipFile(wheels[0]) as wheel:
        contents = set(wheel.namelist())

    assert "alert_axolotl_evo/fitness/__init__.py" in contents
    assert "alert_axolotl_evo/fitness/alignment.py" in contents
    assert "alert_axolotl_evo/fitness/baselines.py" in contents
    assert "alert_axolotl_evo/fitness/evaluator.py" in contents
