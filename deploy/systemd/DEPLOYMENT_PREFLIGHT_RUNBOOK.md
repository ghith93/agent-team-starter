# Queue deployment preflight and activation runbook

## Status

These files are deployment templates, not proof of a running service. The repository preflight is non-mutating. No host is changed by running it.

## 1. Preflight (dry-run)

From a checkout of the repository:

```bash
bash deploy/systemd/preflight-deploy.sh
```

To inspect host-specific prerequisites as the account that will perform deployment:

```bash
sudo bash deploy/systemd/preflight-deploy.sh --host-checks \
  --install-root /opt/agent-team-starter \
  --state-dir /var/lib/agent-team \
  --env-file /etc/agent-team/worker.env \
  --health-env-file /etc/agent-team/health.env
```

The script does not install, enable, restart, or modify services. Host checks verify basic presence/readability/writability; they do not prove provider API access or end-to-end job execution. On systems without `systemd-analyze`, unit syntax verification is explicitly skipped.

## 2. Prepare configuration securely

- Install the application into `/opt/agent-team-starter` and create its virtual environment using the project setup instructions.
- Create a dedicated `agent-team` service account and the state directory `/var/lib/agent-team`; ensure the service account can write only where required.
- Store provider configuration in `/etc/agent-team/worker.env`, owned by root and readable only by root and the service account as required by the host's systemd setup. Never commit secrets.
- Optional health alert configuration belongs in `/etc/agent-team/health.env`; keep it owner-readable only (typically mode 600). Set `ALERT_WEBHOOK_URL` only to a trusted HTTPS endpoint. The URL is a secret; do not paste it into tickets or logs.
- The health alert sends only a generic failure message. If no webhook is configured, failures are recorded in the local journal only.

## 3. Review and install units (explicit operator action)

Review every unit and path before copying. Example only, to be adapted to the host:

```bash
sudo install -o root -g root -m 0644 deploy/systemd/*.service deploy/systemd/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

Do not copy a wildcard if unrelated unit files are present; inspect the source list first. Enable only after confirming environment, directories, ownership, and provider credentials:

```bash
sudo systemctl enable --now agent-team-worker.service
sudo systemctl enable --now agent-team-queue-backup.timer
sudo systemctl enable --now agent-team-queue-health.timer
sudo systemctl enable --now agent-team-queue-restore-test.timer
```

The commands above start/enable host services and are intentionally not run by repository automation.

## 4. Verify after activation

```bash
systemctl --no-pager --full status agent-team-worker.service
systemctl list-timers --all 'agent-team-*'
journalctl -u agent-team-worker.service --since '30 minutes ago' --no-pager
journalctl -u agent-team-queue-health.service --since '30 minutes ago' --no-pager
journalctl -u agent-team-queue-restore-test.service --since '24 hours ago' --no-pager
```

Verify a known harmless test job end to end, confirm a fresh backup exists, and check the restore-test timer completed successfully. A green unit status alone does not prove the provider can execute tasks.

## 5. Rollback

```bash
sudo systemctl disable --now agent-team-worker.service
sudo systemctl disable --now agent-team-queue-backup.timer agent-team-queue-health.timer agent-team-queue-restore-test.timer
```

If reverting the application, preserve the queue database and backups first. Do not delete `/var/lib/agent-team` as part of rollback. Restore a backup to a new path, verify it with `queue_admin status`, and only then plan a controlled cutover.

## Known limitations

- SQLite stores task text in plaintext; do not enqueue secrets or sensitive personal data.
- Provider calls may be repeated if a worker crashes after a provider responds but before the result is committed.
- Local backups are not off-host backups. A host or disk failure can destroy both the queue and its local backups.
- This runbook and the unit templates do not imply that a production host, webhook, or external backup target has been configured.
