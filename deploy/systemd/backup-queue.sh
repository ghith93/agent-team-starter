#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

APP_DIR="${APP_DIR:-/opt/agent-team-starter}"
PYTHON="${PYTHON:-$APP_DIR/.venv/bin/python}"
QUEUE_DB="${QUEUE_DB:-/var/lib/agent-team/queue.sqlite3}"
BACKUP_DIR="${BACKUP_DIR:-/var/lib/agent-team/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

if [[ ! -x "$PYTHON" ]]; then
  echo "Backup failed: configured Python interpreter is not executable." >&2
  exit 2
fi
if [[ ! -f "$QUEUE_DB" ]]; then
  echo "Backup skipped: queue database does not exist yet."
  exit 0
fi
if ! [[ "$RETENTION_DAYS" =~ ^[1-9][0-9]*$ ]]; then
  echo "Backup failed: RETENTION_DAYS must be a positive integer." >&2
  exit 2
fi

install -d -m 0700 "$BACKUP_DIR"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
destination="$BACKUP_DIR/queue-$timestamp.sqlite3"

# queue_admin verifies the backup and refuses to overwrite an existing path.
"$PYTHON" -m agent_team.queue_admin backup --database "$QUEUE_DB" --destination "$destination"

# Apply retention only after a new backup has passed its integrity check.
find "$BACKUP_DIR" -maxdepth 1 -type f -name 'queue-*.sqlite3' -mtime "+$RETENTION_DAYS" -delete
printf 'Backup complete; retention policy: %s days.\n' "$RETENTION_DAYS"
