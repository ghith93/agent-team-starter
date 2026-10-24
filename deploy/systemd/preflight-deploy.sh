#!/usr/bin/env bash
# Non-mutating deployment preflight. It never installs units or starts services.
set -Eeuo pipefail
umask 077

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
INSTALL_ROOT="${INSTALL_ROOT:-/opt/agent-team-starter}"
STATE_DIR="${STATE_DIR:-/var/lib/agent-team}"
ENV_FILE="${ENV_FILE:-/etc/agent-team/worker.env}"
HEALTH_ENV_FILE="${HEALTH_ENV_FILE:-/etc/agent-team/health.env}"
HOST_CHECKS=false
DRY_RUN=true

usage() {
  cat <<'USAGE'
Usage: preflight-deploy.sh [--host-checks] [--install-root PATH] [--state-dir PATH]
                           [--env-file PATH] [--health-env-file PATH] [--dry-run]
Non-mutating by default. --host-checks checks local user/directories/permissions.
No files are installed, changed, or services started.
USAGE
}
while (($#)); do
  case "$1" in
    --host-checks) HOST_CHECKS=true ;;
    --install-root) (($# >= 2)) || { usage >&2; exit 2; }; INSTALL_ROOT="$2"; shift ;;
    --state-dir) (($# >= 2)) || { usage >&2; exit 2; }; STATE_DIR="$2"; shift ;;
    --env-file) (($# >= 2)) || { usage >&2; exit 2; }; ENV_FILE="$2"; shift ;;
    --health-env-file) (($# >= 2)) || { usage >&2; exit 2; }; HEALTH_ENV_FILE="$2"; shift ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Preflight failed: unknown argument." >&2; usage >&2; exit 2 ;;
  esac
  shift
done

errors=0
warn() { printf 'WARN: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1" >&2; errors=$((errors + 1)); }
ok() { printf 'OK: %s\n' "$1"; }

required=(
  agent_team/cli.py
  agent_team/queue_admin.py
  agent_team/workflow_store.py
  deploy/systemd/agent-team-worker.service
  deploy/systemd/agent-team-queue-backup.service
  deploy/systemd/agent-team-queue-backup.timer
  deploy/systemd/agent-team-queue-health.service
  deploy/systemd/agent-team-queue-health.timer
  deploy/systemd/agent-team-queue-restore-test.service
  deploy/systemd/agent-team-queue-restore-test.timer
  deploy/systemd/backup-queue.sh
  deploy/systemd/check-queue-health.sh
  deploy/systemd/run-queue-health-with-alert.sh
  deploy/systemd/test-queue-restore.sh
)
for item in "${required[@]}"; do
  if [[ -f "$ROOT_DIR/$item" ]]; then :; else fail "required deployment file is missing: $item"; fi
done
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  ok "project virtualenv Python is executable"
elif command -v python3 >/dev/null 2>&1; then
  warn "project virtualenv is absent; system Python exists, but service expects the project virtualenv"
else
  fail "neither project virtualenv Python nor python3 is available"
fi

for script in "$ROOT_DIR"/deploy/systemd/*.sh; do
  [[ -f "$script" ]] || continue
  if bash -n "$script"; then :; else fail "shell syntax check failed for $(basename "$script")"; fi
done

if command -v systemd-analyze >/dev/null 2>&1; then
  units=()
  for unit in "$ROOT_DIR"/deploy/systemd/*.service "$ROOT_DIR"/deploy/systemd/*.timer; do
    [[ -f "$unit" ]] && units+=("$unit")
  done
  if (("${#units[@]}" > 0)) && systemd-analyze verify "${units[@]}" >/dev/null 2>&1; then
    ok "systemd unit syntax verified"
  else
    fail "systemd unit verification failed; inspect systemd-analyze output locally"
  fi
else
  warn "systemd-analyze unavailable; unit validation skipped (normal in some containers)"
fi

validate_env_file() {
  local file="$1" label="$2" mode
  if [[ ! -e "$file" ]]; then warn "$label is not present; host configuration remains incomplete"; return; fi
  if [[ ! -f "$file" || -L "$file" ]]; then fail "$label must be a regular non-symlink file"; return; fi
  if command -v stat >/dev/null 2>&1; then
    mode="$(stat -c '%a' "$file" 2>/dev/null || true)"
    if [[ -n "$mode" ]] && (( (8#$mode & 077) != 0 )); then
      fail "$label permissions are too broad; restrict access to owner only (for example chmod 600)"
    else
      ok "$label permissions are owner-only"
    fi
  fi
}
validate_env_file "$ENV_FILE" "worker environment file"
validate_env_file "$HEALTH_ENV_FILE" "health environment file"

if [[ -e "$HEALTH_ENV_FILE" && -f "$HEALTH_ENV_FILE" && ! -L "$HEALTH_ENV_FILE" ]]; then
  # Read only the one expected assignment; never print its value.
  webhook_line="$(grep -E '^[[:space:]]*ALERT_WEBHOOK_URL=' "$HEALTH_ENV_FILE" | tail -n 1 || true)"
  if [[ -n "$webhook_line" ]]; then
    webhook_value="${webhook_line#*=}"
    webhook_value="${webhook_value%\"}"; webhook_value="${webhook_value#\"}"
    webhook_value="${webhook_value%\'}"; webhook_value="${webhook_value#\'}"
    if [[ "$webhook_value" =~ ^https://[^[:space:][:cntrl:]]+$ ]]; then
      ok "configured webhook uses HTTPS and contains no whitespace/control characters"
    else
      fail "ALERT_WEBHOOK_URL is malformed; expected an HTTPS URL without whitespace"
    fi
    unset webhook_value webhook_line
  else
    warn "no webhook configured; health failures will only be visible in the local journal"
  fi
fi

if [[ "$HOST_CHECKS" == true ]]; then
  if id agent-team >/dev/null 2>&1; then ok "agent-team service account exists"; else fail "agent-team service account is missing"; fi
  if [[ -d "$INSTALL_ROOT" && -r "$INSTALL_ROOT" ]]; then ok "install root exists and is readable"; else fail "install root is missing or unreadable"; fi
  if [[ -d "$STATE_DIR" && -w "$STATE_DIR" ]]; then ok "state directory exists and is writable by current user"; else fail "state directory is missing or not writable by current user"; fi
else
  warn "host checks not requested; service account, install root, and state directory were not inspected"
fi

if (( errors > 0 )); then
  printf 'Preflight FAILED: %d issue(s). No deployment changes were made.\n' "$errors" >&2
  exit 1
fi
printf 'Preflight PASSED. Dry-run only; no files installed and no services started.\n'
