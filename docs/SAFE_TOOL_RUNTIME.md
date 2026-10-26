# Bounded agent tools

The agent team can optionally use a small allowlist of read-only tools during the draft stage. This is deliberately narrower than a general shell/browser agent.

## Available tools

- `search_repository`: bounded text search across source and documentation files.
- `read_repository_file`: read one allowlisted UTF-8 source/documentation file.
- `search_public_web`: search public web results through DuckDuckGo's HTML results page.
- `fetch_public_url`: fetch a public HTML/text page and extract readable text.

The model requests tools using a strict JSON action format. Only registered tool names can execute. Calls are capped (default 3; hard maximum 5), output is bounded, errors are sanitized, and tool names/statuses—not arguments or returned page content—are added to stage trace metadata. Tool results are untrusted data and must not override the agent's role or user task.

## Enable locally

```bash
python -m agent_team.cli --tools "Research this repository and summarize the relevant files"
```

Without `--tools`, the existing planner/executor/reviewer/reviser flow remains unchanged. The tool loop runs only for the draft stage and can make up to three additional model requests, so it may consume more free-provider quota.

## Public-web access is separately constrained

Public search and page fetching fail closed unless `AGENT_TEAM_TRUSTED_EGRESS_PROXY` points to an administrator-controlled HTTP(S) egress proxy. The proxy must enforce public destination IP policy after DNS resolution and on every connection, blocking private, loopback, link-local, reserved and cloud metadata destinations. The code also rejects unsafe URLs, blocks redirects, caps response sizes, disables inherited proxy environment settings, and validates result destinations. These controls are defense in depth, not a replacement for network isolation.

For GitHub Actions, the manual on-demand workflow has a separate `enable_tools` checkbox, default false. If public-web access is desired, configure the trusted proxy URL as the Actions secret `AGENT_TEAM_TRUSTED_EGRESS_PROXY`. The workflow already requires explicit `authorize_provider_calls` before any model request. Enabling tools does not bypass that authorization, enable paid models, or activate scheduled runs.

## Current limitations

- These are read-only tools; no shell execution, file writes, package installation, Git commits, pushes, PR creation, or account actions are available to the model.
- Search is HTML-based and may be rate-limited or change format. Returned sources must be checked for relevance and credibility.
- Tool selection is a bounded JSON-in-text protocol rather than native provider tool calling; unsupported response formats fall back to ordinary text output.
- This is not a full browser or OS-level sandbox. Do not expose it as a public service without isolated execution and independently verified network egress policy.
- This feature does not install or automatically adopt OpenHands, Open SWE, LangGraph, or third-party tools. Framework adoption remains evidence-driven; see the open-source tool radar.
