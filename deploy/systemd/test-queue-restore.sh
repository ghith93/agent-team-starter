#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

APP_DIR="${APP_DIR:-/opt/agent-team-starter}"
PYTHON="${PYTHON:-$APP_DIR/.venv/bin/python}"
QUEUE_DB="${QUEUE_DB:-/var/lib/agent-team/queue.sqlite3}"
BACKUP_DIR="${BACKUP_DIR:-/var/lib/agent-team/backups}"
RESTORE_TEST_DIR="${RESTORE_TEST_DIR:-/var/lib/agent-team/restore-test}"

if [[ ! -x "$PYTHON" ]]; then
  echo "Restore test failed: configured Python interpreter is not executable." >&2
  exit 2
fi
if [[ ! -f "$QUEUE_DB" ]]; then
  echo "Restore test skipped: queue database has not been created yet."
  exit 0
fi
if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "Restore test failed: backup directory is missing." >&2
  exit 1
fi

latest_backup="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'queue-*.sqlite3' -printf '%T@ %p\n' | sort -nr | sed -n '1p' || true)"
if [[ -z "$latest_backup" ]]; then
  echo "Restore test failed: no queue backup was found." >&2
  exit 1
fi
backup_path="${latest_backup#* }"

install -d -m 0700 "$RESTORE_TEST_DIR"
temporary_dir="$(mktemp -d "$RESTORE_TEST_DIR/run.XXXXXXXX")"
cleanup() { rm -rf -- "$temporary_dir"; }
trap cleanup EXIT INT TERM

restored_db="$temporary_dir/queue-restored.sqlite3"
"$PYTHON" -m agent_team.queue_admin restore --backup "$backup_path" --destination "$restored_db" >/dev/null
"$PYTHON" -m agent_team.queue_admin status --database "$restored_db" >/dev/null
echo "Restore test passed: newest backup restored and opened successfully; temporary copy will be removed."
