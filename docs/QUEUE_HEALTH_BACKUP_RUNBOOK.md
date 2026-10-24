# Queue health and backup runbook

The queue admin commands are local-only and do not call model providers.

## Health/status

```bash
python -m agent_team.queue_admin status --database "$HOME/.agent-team/queue.sqlite3"
```

The command returns SQLite integrity status, aggregate counts for queued/running/succeeded/failed jobs, and the number of expired leases. It never prints task text or generated results.

## Consistent backup

```bash
umask 077
python -m agent_team.queue_admin backup \
  --database "$HOME/.agent-team/queue.sqlite3" \
  --destination "$HOME/.agent-team/backups/queue-$(date +%Y%m%d-%H%M%S).sqlite3"
```

The command uses SQLite's backup API, checks the copied database, refuses to overwrite an existing destination, and applies owner-only permissions on POSIX systems. Keep backups encrypted and in an access-controlled location if task content could be sensitive. Backups contain queued task text in plaintext at the SQLite layer.

## Restore test

Restore into a new path, never over the live database:

```bash
python -m agent_team.queue_admin restore \
  --backup "$HOME/.agent-team/backups/queue-YYYYMMDD-HHMMSS.sqlite3" \
  --destination "$HOME/.agent-team/restore-test/queue.sqlite3"
python -m agent_team.queue_admin status \
  --database "$HOME/.agent-team/restore-test/queue.sqlite3"
```

Review the counts and integrity result before treating a backup as usable. A backup command succeeding is not the same as a tested recovery process; periodically run the restore test and retain its evidence.

## Monitoring and scheduling

Run the `status` command from a host scheduler or monitoring agent to collect health/counts, and alert on failed jobs, old queued jobs, expired leases, or a failed integrity check. Configure this outside the Python project. The repository does not currently install a scheduler, alert delivery integration, remote backup destination, or 24/7 host supervisor.
