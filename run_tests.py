"""Run the full offline regression and reference-evaluation suites."""
import subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parent
commands = [
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [sys.executable, "-m", "unittest", "discover", "-s", "evaluations", "-p", "test_*.py", "-v"],
    [sys.executable, str(root / "evaluations" / "reference_evaluator.py")],
    [sys.executable, str(root / "evaluations" / "prompt_injection_suite.py")],
    [sys.executable, str(root / "evaluations" / "security_audit.py")],
    [sys.executable, "-m", "unittest", "discover", "-s", "evaluations", "-p", "test_archive_audit.py", "-v"],
]
for command in commands:
    print("\n$", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=root)
    if result.returncode:
        print("FAIL: stopped; release not approved.")
        raise SystemExit(result.returncode)
print("\nALL OFFLINE CHECKS PASSED. This does not establish live-model quality.")
