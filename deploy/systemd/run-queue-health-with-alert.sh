#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

APP_DIR="${APP_DIR:-/opt/agent-team-starter}"
HEALTH_CHECK_SCRIPT="${HEALTH_CHECK_SCRIPT:-$APP_DIR/deploy/systemd/check-queue-health.sh}"
CURL_BIN="${CURL_BIN:-$(command -v curl || true)}"

if [[ ! -f "$HEALTH_CHECK_SCRIPT" ]]; then
  echo "Health alert wrapper failed: health-check script is missing." >&2
  exit 2
fi

if /bin/bash "$HEALTH_CHECK_SCRIPT"; then
  exit 0
else
  health_status=$?
fi

if [[ -z "${ALERT_WEBHOOK_URL:-}" ]]; then
  echo "Health check failed; no ALERT_WEBHOOK_URL configured, see local system journal." >&2
  exit "$health_status"
fi
if [[ ! "$ALERT_WEBHOOK_URL" =~ ^https:// ]]; then
  echo "Health check failed; ALERT_WEBHOOK_URL requires an HTTPS URL; alert not sent." >&2
  exit "$health_status"
fi
if [[ -z "$CURL_BIN" || ! -x "$CURL_BIN" ]]; then
  echo "Health check failed; curl is unavailable, alert not sent." >&2
  exit "$health_status"
fi

payload='{"text":"Agent Team queue health check failed. Inspect the host system journal for details."}'
if ! "$CURL_BIN" --fail --silent --show-error --max-time 5 \
  --header "Content-Type: application/json" \
  --data "$payload" "$ALERT_WEBHOOK_URL"; then
  echo "Health check failed and webhook delivery failed." >&2
else
  echo "Health check failed; generic webhook alert sent."
fi
exit "$health_status"
