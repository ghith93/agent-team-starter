#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

APP_DIR="${APP_DIR:-/opt/agent-team-starter}"
PYTHON="${PYTHON:-$APP_DIR/.venv/bin/python}"
QUEUE_DB="${QUEUE_DB:-/var/lib/agent-team/queue.sqlite3}"
MAX_QUEUED_AGE_SECONDS="${MAX_QUEUED_AGE_SECONDS:-900}"
MAX_RUNNING_AGE_SECONDS="${MAX_RUNNING_AGE_SECONDS:-1800}"
BACKUP_DIR="${BACKUP_DIR:-/var/lib/agent-team/backups}"
MAX_BACKUP_AGE_SECONDS="${MAX_BACKUP_AGE_SECONDS:-172800}"
FAIL_ON_FAILED_JOBS="${FAIL_ON_FAILED_JOBS:-true}"
LOCK_DIR="${LOCK_DIR:-/var/lib/agent-team}"
LOCK_FILE="$LOCK_DIR/.health-check.lock"

if [[ ! -x "$PYTHON" ]]; then
  echo "Health check failed: configured Python interpreter is not executable." >&2
  exit 2
fi
if [[ ! -f "$QUEUE_DB" ]]; then
  echo "Health check: queue database has not been created yet; no jobs to inspect."
  exit 0
fi
for threshold in "$MAX_QUEUED_AGE_SECONDS" "$MAX_RUNNING_AGE_SECONDS" "$MAX_BACKUP_AGE_SECONDS"; do
  if ! [[ "$threshold" =~ ^[0-9]+$ ]]; then
    echo "Health check failed: age thresholds must be non-negative integers." >&2
    exit 2
  fi
done
if [[ "$FAIL_ON_FAILED_JOBS" != "true" && "$FAIL_ON_FAILED_JOBS" != "false" ]]; then
  echo "Health check failed: FAIL_ON_FAILED_JOBS must be true or false." >&2
  exit 2
fi

install -d -m 0700 "$LOCK_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Health check skipped: another check holds the lock."
  exit 0
fi

args=(status --database "$QUEUE_DB"
  --fail-on-expired-leases
  --max-queued-age-seconds "$MAX_QUEUED_AGE_SECONDS"
  --max-running-age-seconds "$MAX_RUNNING_AGE_SECONDS")
if [[ "$FAIL_ON_FAILED_JOBS" == "true" ]]; then
  args+=(--fail-on-failed-jobs)
fi

# A healthy queue is not sufficient if its recovery point is too old or unusable.
if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "Health check failed: backup directory is missing." >&2
  exit 1
fi
latest_backup="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'queue-*.sqlite3' -printf '%T@ %p\n' | sort -nr | sed -n '1p' || true)"
if [[ -z "$latest_backup" ]]; then
  echo "Health check failed: no queue backup was found." >&2
  exit 1
fi
backup_mtime="${latest_backup%% *}"
backup_path="${latest_backup#* }"
now="$(date +%s)"
backup_age="$(awk -v now="$now" -v mtime="$backup_mtime" 'BEGIN { age = now - mtime; if (age < 0) age = 0; printf "%d", age }')"
if (( backup_age > MAX_BACKUP_AGE_SECONDS )); then
  echo "Health check failed: latest queue backup exceeds the configured age threshold." >&2
  exit 1
fi
if ! "$PYTHON" -m agent_team.queue_admin status --database "$backup_path" >/dev/null 2>&1; then
  echo "Health check failed: latest queue backup cannot be opened or failed its integrity check." >&2
  exit 1
fi
echo "Health check: latest queue backup is recent and readable."

exec "$PYTHON" -m agent_team.queue_admin "${args[@]}"
