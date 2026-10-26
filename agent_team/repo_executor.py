"""Evaluate a proposed unified diff in a disposable copy of a repository.

The caller's checkout is never modified. Only fixed, named validation commands are allowed;
model-supplied shell commands are never executed.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec B404: subprocess is used only with fixed argument lists and shell=False.
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
from .sandbox import run_sandboxed_command

MAX_PATCH_BYTES = 200_000
MAX_CHANGED_PATHS = 50
MAX_TIMEOUT_SECONDS = 300
MAX_WORKSPACE_FILES = 5000
MAX_WORKSPACE_BYTES = 100_000_000
MAX_PATCH_DIAGNOSTIC_CHARS = 240


def _safe_patch_diagnostic(value: object) -> str:
    """Keep useful patch-tool diagnostics bounded and redact credential-like values."""
    detail = " ".join(str(value).split())
    detail = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]", detail)
    detail = re.sub(r"(?i)(api[_ -]?key|token|authorization)(\s*[:=]\s*)[^,; ]+", r"\1\2[REDACTED]", detail)
    return detail[:MAX_PATCH_DIAGNOSTIC_CHARS]
VALIDATION_COMMANDS = {
    "project-tests": ("python", "run_tests.py"),
    "pytest": ("python", "-m", "pytest", "-q"),
    "unittest": ("python", "-m", "unittest", "discover", "-v"),
    "compile": ("python", "-m", "compileall", "-q", "agent_team", "tests"),
}
PROTECTED_PARTS = {".git", ".ssh", ".aws", ".azure", ".config", "secrets", "credentials"}
PROTECTED_NAMES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519"}
PROTECTED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


class PatchRejected(ValueError):
    """A patch was rejected before any candidate code was executed."""


@dataclass(frozen=True)
class ValidationResult:
    command: str
    passed: bool
    returncode: int | None
    timed_out: bool
    output: str


@dataclass(frozen=True)
class PatchEvaluation:
    accepted: bool
    applied_in_temporary_copy: bool
    changed_paths: tuple[str, ...]
    validations: tuple[ValidationResult, ...]
    message: str

    def to_dict(self) -> dict:
        return asdict(self)


def _validate_patch(patch: str) -> tuple[str, ...]:
    if not isinstance(patch, str) or not patch.strip():
        raise PatchRejected("Patch must be non-empty text.")
    if len(patch.encode("utf-8")) > MAX_PATCH_BYTES:
        raise PatchRejected(f"Patch exceeds {MAX_PATCH_BYTES} bytes.")
    if "\x00" in patch:
        raise PatchRejected("Patch contains a NUL byte.")
    if not (patch.startswith("diff --git ") or patch.startswith("--- ")):
        raise PatchRejected("Expected a unified git diff.")
    if re.search(r"(?m)^GIT binary patch$|^Binary files .* differ$", patch):
        raise PatchRejected("Binary patches are not supported.")

    paths: set[str] = set()
    old_headers: list[str] = []
    new_headers: list[str] = []
    for line in patch.splitlines():
        if not (line.startswith("+++ ") or line.startswith("--- ")):
            continue
        is_old = line.startswith("--- ")
        raw = line[4:].split("\t", 1)[0].strip()
        if raw == "/dev/null":
            (old_headers if is_old else new_headers).append(raw)
            continue
        expected_prefix = "a/" if is_old else "b/"
        if not raw.startswith(expected_prefix):
            label = "old-file" if is_old else "new-file"
            raise PatchRejected(f"Malformed {label} header; expected '{expected_prefix}<path>' or /dev/null.")
        (old_headers if is_old else new_headers).append(raw)
        raw = raw[2:]
        path = PurePosixPath(raw)
        if path.is_absolute() or "\\" in raw or not raw or any(part in ("", ".", "..") for part in path.parts):
            raise PatchRejected("Patch contains an unsafe path.")
        lowered = [part.lower() for part in path.parts]
        if any(part in PROTECTED_PARTS for part in lowered):
            raise PatchRejected("Patch touches a protected credentials/configuration path.")
        if path.name.lower() in PROTECTED_NAMES or path.suffix.lower() in PROTECTED_SUFFIXES:
            raise PatchRejected("Patch touches a protected secret-like file.")
        if lowered[0] == ".github" and len(lowered) > 1 and lowered[1] == "workflows":
            raise PatchRejected("Workflow changes require separate human review.")
        paths.add(path.as_posix())
    if not old_headers or len(old_headers) != len(new_headers):
        raise PatchRejected("Patch must contain matching old-file and new-file headers.")
    for old_path, new_path in zip(old_headers, new_headers):
        if old_path == "/dev/null" and new_path == "/dev/null":
            raise PatchRejected("Patch cannot use /dev/null for both file headers.")
        if old_path != "/dev/null" and new_path != "/dev/null" and old_path[2:] != new_path[2:]:
            raise PatchRejected("Old-file and new-file headers must name the same path.")
    if re.search(r"(?m)^(?:new|old) file mode 120000$|^Subproject commit ", patch):
        raise PatchRejected("Symlink and submodule patches are not supported.")
    if re.search(r"(?m)^(?:rename|copy) (?:from|to) ", patch):
        raise PatchRejected("Rename and copy patches are not supported.")
    if not paths:
        raise PatchRejected("No changed file paths were found in the patch.")
    if len(paths) > MAX_CHANGED_PATHS:
        raise PatchRejected(f"Patch touches more than {MAX_CHANGED_PATHS} paths.")
    return tuple(sorted(paths))


def _ignore_copy(_directory: str, names: list[str]) -> set[str]:
    ignored = set()
    for name in names:
        low = name.lower()
        if (
            low == ".git"
            or low in {".venv", "venv", "__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".tox"}
            or low in PROTECTED_NAMES
            or low in PROTECTED_PARTS
            or low.endswith((".pem", ".key", ".p12", ".pfx"))
            or low.startswith(".env")
        ):
            ignored.add(name)
    return ignored


def _run_validation(
    candidate: Path, name: str, timeout_seconds: int, trusted_requirements_root: Path | None = None,
) -> ValidationResult:
    if name in {"project-tests", "pytest", "unittest"}:
        sandbox = run_sandboxed_command(
            candidate,
            trusted_requirements_root or candidate,
            VALIDATION_COMMANDS[name],
            name,
            timeout_seconds,
        )
        return ValidationResult(name, sandbox.passed, sandbox.returncode, sandbox.timed_out, sandbox.output)
    try:
        completed = subprocess.run(  # nosec B603: fixed command allowlist; shell=False and environment is restricted.
            VALIDATION_COMMANDS[name],
            cwd=candidate,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            shell=False,
            env={
                "PATH": os.environ.get("PATH", ""),
                "HOME": str(candidate),
                "TMPDIR": str(candidate),
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONIOENCODING": "utf-8",
            },
        )
        return ValidationResult(name, completed.returncode == 0, completed.returncode,
                                False, completed.stdout[-12000:])
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return ValidationResult(name, False, None, True, str(output)[-12000:])


def evaluate_patch(
    workspace: str | Path,
    patch: str,
    validations: Iterable[str] = ("compile",),
    timeout_seconds: int = 120,
) -> PatchEvaluation:
    """Apply a proposed diff in a disposable copy and run fixed local checks.

    Passing checks is not proof of correctness or security. No changes are applied to the
    original checkout, and this helper never commits, pushes, or merges.
    """
    changed_paths = _validate_patch(patch)
    root = Path(workspace).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("Workspace must be an existing directory.")
    selected = tuple(dict.fromkeys(validations))
    if not selected:
        raise ValueError("Select at least one validation command.")
    if any(name not in VALIDATION_COMMANDS for name in selected):
        raise ValueError("Unknown validation command name.")
    if not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS:
        raise ValueError(f"timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}.")

    file_count = 0
    total_bytes = 0
    for current, dirs, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in list(dirs):
            item = current_path / name
            if item.is_symlink():
                raise ValueError("Workspace contains a symbolic link; refusing to copy it.")
        for name in files:
            item = current_path / name
            if item.is_symlink():
                raise ValueError("Workspace contains a symbolic link; refusing to copy it.")
            try:
                total_bytes += item.stat().st_size
            except OSError as exc:
                raise ValueError("Workspace contains an unreadable file.") from exc
            file_count += 1
            if file_count > MAX_WORKSPACE_FILES or total_bytes > MAX_WORKSPACE_BYTES:
                raise ValueError("Workspace exceeds the safe copy size limits.")

    with tempfile.TemporaryDirectory(prefix="agent-team-candidate-") as temp:
        temp_root = Path(temp)
        candidate = temp_root / "workspace"
        shutil.copytree(root, candidate, ignore=_ignore_copy, symlinks=False)
        patch_file = temp_root / "candidate.patch"
        patch_file.write_text(patch, encoding="utf-8")
        check = subprocess.run(  # nosec B603: fixed git command; shell=False.
            ("git", "apply", "--check", "--whitespace=error", str(patch_file)),
            cwd=candidate, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, errors="replace", timeout=30,
            check=False, shell=False,
        )
        if check.returncode:
            detail = _safe_patch_diagnostic(check.stdout)
            message = "Patch did not apply cleanly; validation was not run."
            if detail:
                message += f" Diagnostic: {detail}"
            return PatchEvaluation(False, False, changed_paths, (), message)
        applied = subprocess.run(  # nosec B603: fixed git command; shell=False.
            ("git", "apply", "--whitespace=error", str(patch_file)),
            cwd=candidate, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, errors="replace", timeout=30,
            check=False, shell=False,
        )  # nosec B603: fixed git executable and arguments; shell is disabled.
        if applied.returncode:
            return PatchEvaluation(False, False, changed_paths, (),
                                   "Patch application failed; validation was not run.")
        results = tuple(_run_validation(candidate, name, timeout_seconds, root) for name in selected)
        passed = all(result.passed for result in results)
        return PatchEvaluation(
            passed, True, changed_paths, results,
            "Selected validations passed in a disposable copy." if passed
            else "One or more validations failed in a disposable copy; inspect the results.",
        )
