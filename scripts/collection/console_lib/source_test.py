"""Run only the project-owned source_tests/test.py diagnostic program."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_source_test(collection_root: Path, source_id: str) -> dict[str, object]:
    script = collection_root / "source_tests" / "test.py"
    if not script.is_file():
        raise FileNotFoundError(f"test.py not found: {script}")
    completed = subprocess.run(
        [sys.executable, str(script), "--source", source_id],
        cwd=str(collection_root), capture_output=True, text=True, timeout=60, check=False,
    )
    return {"command": [sys.executable, str(script), "--source", source_id], "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
