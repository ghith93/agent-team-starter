# Queue health and backup runbook

The queue admin commands are local-only and do not call model providers.

## Health/status

```bash
python -m agent_team.queue_admin status --database "$HOME/.agent-team/queue.sqlite3"
```

The command returns SQLite integrity status, aggregate counts for queued/running/succeeded/failed jobs, the number of expired leases, and the age of the oldest queued and running jobs. It never prints task text or generated results.

Use threshold flags when invoking it from cron, systemd, or a monitoring agent. A non-zero exit code signals that an alert condition was met:

```bash
# Fail if there are any expired worker leases or terminally failed jobs.
python -m agent_team.queue_admin status \
  --database "$HOME/.agent-team/queue.sqlite3" \
  --fail-on-expired-leases --fail-on-failed-jobs

# Fail if the oldest queued job has waited more than 15 minutes.
python -m agent_team.queue_admin status \
  --database "$HOME/.agent-team/queue.sqlite3" \
  --max-queued-age-seconds 900
```

The status command does not send notifications itself; use the scheduler/monitor to route non-zero exits to an alert channel.

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

## Automated health checks

The systemd templates can run a local health check every five minutes. It emits aggregate queue status and threshold names, not task text or results. Defaults are 15 minutes for queued tasks, 30 minutes for running tasks, and 48 hours for the newest local backup. Expired leases, terminal failures, a missing backup directory, no matching backup, an unreadable/corrupt backup, or an overdue latest backup are unhealthy by default. The health check opens the newest backup through the queue admin read-only status command; it does not print the backup's task contents. Configure `MAX_QUEUED_AGE_SECONDS`, `MAX_RUNNING_AGE_SECONDS`, `MAX_BACKUP_AGE_SECONDS`, `BACKUP_DIR`, and `FAIL_ON_FAILED_JOBS` through a root-managed `/etc/agent-team/health.env` file.

The backup freshness check runs only after the queue database exists; before initial queue creation, the health check reports that there are no jobs to inspect and exits successfully. The health service runs as `agent-team`; ensure backup files and the directory are readable by that account while keeping them owner-restricted.

A non-zero health-check exit is recorded in the local system journal. This is local monitoring, not an external notification: route service failures to a real alerting destination separately if remote notification is required.
