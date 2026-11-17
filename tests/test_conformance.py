import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / "conformance" / "runner.py"

def test_conformance_suite():
    p = subprocess.run([sys.executable, str(RUNNER)], capture_output=True, text=True, encoding="utf-8")
    assert p.returncode == 0, p.stdout + p.stderr
