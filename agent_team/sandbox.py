"""Run candidate project tests inside a network-disabled Docker container.

The Docker image is built from the original workspace's sanitized dependency list. Candidate
code runs only after the image is built, with no network, no host credentials, a read-only
container root filesystem, resource limits, and the disposable candidate workspace as its
only writable bind mount.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid


MAX_OUTPUT_CHARS = 12_000
MAX_BUILD_TIMEOUT_SECONDS = 240
REQUIREMENT_LINE = re.compile(
    r"^[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?"
    r"(?:\s*(?:===|==|~=|!=|>=|<=|>|<)\s*[A-Za-z0-9.*+_-]+)*$"
)


@dataclass(frozen=True)
class SandboxResult:
    passed: bool
    returncode: int | None
    timed_out: bool
    output: str


def _safe_requirements(root: Path) -> tuple[str | None, str | None]:
    path = root / "requirements.txt"
    if not path.exists():
        return "", None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 100_000:
        return None, "Sandbox blocked: requirements.txt is not a regular bounded file."
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, "Sandbox blocked: requirements.txt is not readable UTF-8."
    safe_lines = []
    for line in content.splitlines():
        item = line.strip()
        if not item or item.startswith("#"):
            continue
        if not REQUIREMENT_LINE.fullmatch(item):
            return None, "Sandbox blocked: requirements.txt contains a URL, option, or unsupported dependency syntax."
        safe_lines.append(item)
    return "\n".join(safe_lines) + ("\n" if safe_lines else ""), None


def _restricted_env(home: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", ""),
        "HOME": str(home),
        "TMPDIR": str(home),
        "DOCKER_CONFIG": str(home / "docker-config"),
    }


def _run_docker(args: tuple[str, ...], *, cwd: Path, timeout: int, env: dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603: fixed internal Docker commands; shell=False and no model-supplied command text.
        args,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        timeout=timeout,
        check=False,
        shell=False,
        env=env,
    )


def _redact_output(output: str) -> str:
    output = re.sub(
        r"(?i)(api[_-]?key|secret|password|token)(\s*[:=]\s*)[^\s,;]+",
        r"\1\2[REDACTED]",
        output,
    )
    output = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]+=*", r"\1[REDACTED]", output)
    return output[-MAX_OUTPUT_CHARS:]


def run_sandboxed_command(
    candidate: str | Path,
    trusted_requirements_root: str | Path,
    command: tuple[str, ...],
    validation_name: str,
    timeout_seconds: int,
) -> SandboxResult:
    """Run a fixed validation command in a network-disabled, resource-limited container."""
    candidate_path = Path(candidate).resolve()
    requirements_root = Path(trusted_requirements_root).resolve()
    if not candidate_path.is_dir() or not requirements_root.is_dir():
        return SandboxResult(False, None, False, "Sandbox blocked: workspace is missing.")
    docker = shutil.which("docker")
    if not docker:
        return SandboxResult(False, None, False, "Sandbox unavailable: Docker is required; tests were not run on the host.")
    if not hasattr(os, "getuid") or not hasattr(os, "getgid"):
        return SandboxResult(False, None, False, "Sandbox unavailable: this platform cannot run the configured unprivileged container.")
    requirements, problem = _safe_requirements(requirements_root)
    if problem:
        return SandboxResult(False, None, False, problem)

    image_tag = "agent-team-test:" + uuid.uuid4().hex
    container_name = "agent-team-test-" + uuid.uuid4().hex[:20]
    with tempfile.TemporaryDirectory(prefix="agent-team-sandbox-build-") as temporary:
        build_root = Path(temporary)
        (build_root / "requirements.txt").write_text(requirements or "", encoding="utf-8")
        dockerfile = [
            "FROM python:3.11-slim",
            "ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8",
            "COPY requirements.txt /opt/agent-test/requirements.txt",
            "RUN python -m pip install --no-cache-dir -r /opt/agent-test/requirements.txt",
            "RUN mkdir -p /run/agent-tmp",
        ]
        if validation_name == "pytest":
            dockerfile.append("RUN python -m pip install --no-cache-dir pytest")
        (build_root / "Dockerfile").write_text("\n".join(dockerfile) + "\n", encoding="utf-8")
        (build_root / "docker-config").mkdir()
        env = _restricted_env(build_root)
        try:
            try:
                built = _run_docker(
                    (docker, "build", "--pull", "--tag", image_tag, "--file", str(build_root / "Dockerfile"), str(build_root)),
                    cwd=build_root, timeout=MAX_BUILD_TIMEOUT_SECONDS, env=env,
                )
            except subprocess.TimeoutExpired as exc:
                output = exc.stdout or ""
                if isinstance(output, bytes):
                    output = output.decode("utf-8", errors="replace")
                return SandboxResult(False, None, True, _redact_output(str(output) + "\nSandbox image build timed out."))
            except OSError as exc:
                return SandboxResult(False, None, False, f"Sandbox image build failed ({type(exc).__name__}).")
            if built.returncode != 0:
                return SandboxResult(False, built.returncode, False, _redact_output(built.stdout + "\nSandbox image build failed."))
            mount = f"type=bind,src={candidate_path},dst=/workspace,rw"
            run_args = (
                docker, "run", "--rm", "--name", container_name,
                "--network", "none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--pids-limit=128",
                "--memory=1g",
                "--cpus=2",
                "--tmpfs", "/run/agent-tmp:rw,nosuid,nodev,noexec,size=256m",
                "--mount", mount,
                "--workdir", "/workspace",
                "--user", f"{os.getuid()}:{os.getgid()}",
                "--env", "HOME=/run/agent-tmp",
                "--env", "TMPDIR=/run/agent-tmp",
                "--env", "PYTHONDONTWRITEBYTECODE=1",
                "--env", "PYTHONIOENCODING=utf-8",
                image_tag, *command,
            )
            try:
                completed = _run_docker(run_args, cwd=build_root, timeout=timeout_seconds, env=env)
                return SandboxResult(
                    completed.returncode == 0, completed.returncode, False,
                    _redact_output(completed.stdout),
                )
            except subprocess.TimeoutExpired as exc:
                output = exc.stdout or ""
                if isinstance(output, bytes):
                    output = output.decode("utf-8", errors="replace")
                return SandboxResult(False, None, True, _redact_output(str(output) + "\nSandboxed test command timed out."))
            except OSError as exc:
                return SandboxResult(False, None, False, f"Sandbox test failed ({type(exc).__name__}); no host fallback was attempted.")
            finally:
                # Ensure a timed-out client cannot leave a candidate container running.
                try:
                    _run_docker(
                        (docker, "rm", "--force", container_name),
                        cwd=build_root, timeout=10, env=env,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    pass
        finally:
            try:
                _run_docker(
                    (docker, "image", "rm", "--force", image_tag),
                    cwd=build_root, timeout=20, env=env,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
