# Linux systemd deployment runbook

This is an installation template, not a deployed service. It targets a single Linux host using systemd and the local SQLite queue. It does not create a server or obtain API credentials.

## 1. Prepare a dedicated runtime

Use a supported Linux host with systemd, Python 3.11+, and outbound network access to the configured provider. Install the repository at `/opt/agent-team-starter`, create a virtual environment at `/opt/agent-team-starter/.venv`, and install `requirements.txt`. Keep the checkout owned by root or a deployment account and not writable by the service user.

Create the service account and environment directory:

```bash
sudo useradd --system --home-dir /var/lib/agent-team --create-home --shell /usr/sbin/nologin agent-team
sudo install -d -o root -g root -m 0755 /etc/agent-team
sudo install -d -o agent-team -g agent-team -m 0700 /var/lib/agent-team
sudo install -o root -g root -m 0600 /dev/null /etc/agent-team/worker.env
sudoedit /etc/agent-team/worker.env
```

Put only the provider variables required by the configured router in `/etc/agent-team/worker.env`, such as `GEMINI_API_KEY=...` or `OPENROUTER_API_KEY=...`. Do not commit this file, paste credentials into task text, or expose its contents in logs. Verify the router's current environment variable names before use.

The service uses `/var/lib/agent-team/queue.sqlite3`. Enqueue only non-sensitive tasks as the service account, for example:

```bash
sudo -u agent-team /opt/agent-team-starter/.venv/bin/python -m agent_team.cli \
  --queue-db /var/lib/agent-team/queue.sqlite3 \
  --enqueue --max-attempts 3 "Summarize public release notes"
```

## 2. Install and start the worker

From the repository root:

```bash
sudo install -o root -g root -m 0644 deploy/systemd/agent-team-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now agent-team-worker.service
sudo systemctl status agent-team-worker.service --no-pager
sudo journalctl -u agent-team-worker.service -n 100 --no-pager
```

The unit restarts on process failure and applies systemd hardening. It restricts socket address families to Unix sockets and IPv4/IPv6, but this is not destination-level egress filtering. It expects the repository and virtual environment at the paths above. Review and adapt paths, resource limits, firewall rules, provider terms, and operational ownership for the host. The worker is a single-host service; do not point multiple hosts at a shared network-filesystem SQLite database.

## 3. Enable daily verified backups

The backup script uses the project's SQLite backup API and integrity check. It keeps timestamped backups in `/var/lib/agent-team/backups`, applies owner-only permissions, and prunes matching old backup files only after a new backup succeeds. Default retention is 30 days. Backups contain task text and must be treated as private data.

```bash
sudo install -o root -g root -m 0644 deploy/systemd/agent-team-queue-backup.service /etc/systemd/system/
sudo install -o root -g root -m 0644 deploy/systemd/agent-team-queue-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now agent-team-queue-backup.timer
sudo systemctl start agent-team-queue-backup.service
sudo systemctl status agent-team-queue-backup.service --no-pager
sudo systemctl list-timers agent-team-queue-backup.timer
```

To change retention, add `RETENTION_DAYS=30` or another positive integer to a root-managed systemd drop-in for the backup service. Never set it to a very short interval without confirming recovery requirements.

## 4. Health and restore drills

```bash
sudo -u agent-team /opt/agent-team-starter/.venv/bin/python -m agent_team.queue_admin status \
  --database /var/lib/agent-team/queue.sqlite3
```

Periodically restore a backup to a new path and run `status` against it. Do not restore over the live database. Confirm free disk space, backup age, expired leases, failed jobs, and logs. The supplied units do not deliver external alerts; configure host monitoring and an alert channel separately.

## Security and reliability limits

- These units are templates; this repository change does not provision or configure any host.
- Provider calls may incur usage or quota consumption depending on provider and model selection.
- SQLite stores task text in plaintext. Backups do too at the database layer; use encrypted storage and access controls where appropriate.
- A worker lease cannot guarantee exactly-once provider calls after a crash.
- The backup timer provides local backups, not off-host disaster recovery. Periodically copy encrypted backups to a separate trusted location.
- Do not add a GitHub Actions workflow that starts an infinite worker on a hosted runner; hosted workflow jobs are not a persistent service.


## 5. Enable five-minute queue health monitoring

Install the health script and systemd service/timer alongside the worker. The health check is read-only and emits aggregate counts and alert names only.

```bash
sudo install -o root -g root -m 0644 deploy/systemd/agent-team-queue-health.service /etc/systemd/system/
sudo install -o root -g root -m 0644 deploy/systemd/agent-team-queue-health.timer /etc/systemd/system/
sudo install -o root -g root -m 0644 /dev/null /etc/agent-team/health.env
sudoedit /etc/agent-team/health.env
sudo systemctl daemon-reload
sudo systemctl enable --now agent-team-queue-health.timer
sudo systemctl start agent-team-queue-health.service
sudo journalctl -u agent-team-queue-health.service -n 50 --no-pager
```

Optional settings in the root-managed health environment file include `MAX_QUEUED_AGE_SECONDS=900`, `MAX_RUNNING_AGE_SECONDS=1800`, and `FAIL_ON_FAILED_JOBS=true`. The defaults flag expired leases, queued jobs older than 15 minutes, running jobs older than 30 minutes, and terminal failed jobs. A health check failure is visible in the system journal; it does not by itself send a remote alert. Add an external monitoring/notification route if operators need paging or email.
