# Open-source Tool Radar for Agent Team Starter

**Research date:** 2026-10-23  
**Policy:** zero-cost by default; no installation, account connection, API call, repository mutation, or external execution without explicit approval. Links below point to primary project repositories/docs wherever possible. Project activity and licensing can change; re-check before adoption.

## Recommended stack: add value before adding dependencies

| Priority | Project | Primary value | Suggested use here | Cost / risk notes | Decision |
|---|---|---|---|---|---|
| P0 | [pytest / unittest](https://docs.python.org/3/library/unittest.html) | Repeatable regression tests | Keep deterministic tests in CI/local runner | Already available; no API | Keep baseline |
| P0 | [Gitleaks](https://github.com/gitleaks/gitleaks) | Detect secrets in source/history | Run locally before packaging; inspect findings, never print secret values | External binary not present in current environment; do not install automatically | Candidate for later CI |
| P0 | [pip-audit](https://github.com/pypa/pip-audit) | Known Python dependency vulnerabilities | Audit requirements/environment before release | Vulnerability DB lookup may require network; distinguish offline from online run | Candidate, not run |
| P0 | [Semgrep CE](https://github.com/semgrep/semgrep) | Pattern-based static analysis | Scan SSRF, subprocess, secret, and unsafe URL patterns | Community edition has analysis limits; findings need triage; binary absent | Candidate, not run |
| P0 | [Promptfoo](https://github.com/promptfoo/promptfoo) | LLM/agent evaluations and red-team tests | Highest-value next evaluator for prompt injection, tool-use and regressions | Deterministic assertions can be local; model judging/red-team generation may need a provider/API | Pilot only after offline harness is stable |
| P1 | [ast-grep](https://github.com/ast-grep/ast-grep) | AST-aware search, lint and code rewrites | Find code patterns across Python/JS/JSON and make controlled codemods | CLI absent; rewrites must run on a branch and pass tests | Candidate for code archaeology |
| P1 | [MCP Inspector](https://github.com/modelcontextprotocol/inspector) | Inspect/test MCP server tools and protocol behavior | Verify server discovery, schemas, calls, errors and transport | Node >=22.19.0 noted in current docs; do not expose test server publicly | Candidate for MCP integration tests |
| P1 | [MCP-Scan](https://github.com/iflow-mcp/invariantlabs-ai-mcp-scan) and [docs](https://github.com/invariantlabs-ai/docs/blob/main/docs/mcp-scan/index.md) | Scan MCP configs, tool descriptions, and agent skills for injection/tool-poisoning risks | Use before trusting third-party MCP servers or skill bundles | Project docs disclose that tool names/descriptions may be sent to Invariant services unless opting out; inspect privacy and terms before running | Security review first |
| P1 | [DeepEval](https://deepeval.com/docs/introduction) | Pytest-style LLM/agent evaluation, trajectory and component checks | Add after mapping our 12-task benchmark to its cases | LLM-as-judge needs a provider; local-only mode must be explicit | Not installed; don't install automatically |
| P1 | [OpenHands](https://github.com/All-Hands-AI/OpenHands) | Autonomous software engineering agent | Compare on a disposable copy of the same benchmark tasks | More infrastructure/permissions than current small project; sandboxing mandatory | Compare only, do not replace by popularity |
| P1 | [LangGraph](https://github.com/langchain-ai/langgraph) | Stateful multi-step agent orchestration | Compare only if current router/workflow complexity is demonstrably limiting | Adds framework and maintenance surface | Defer pending benchmark evidence |
| P2 | [Ghidra](https://github.com/NationalSecurityAgency/ghidra) | Static reverse engineering of binaries | Analyze owned/authorized binaries, formats and program behavior | Large Java desktop application; not needed for Python source maintenance | Separate toolbox |
| P2 | [radare2](https://github.com/radareorg/radare2) | CLI binary analysis, disassembly, scripting | Lightweight CLI alternative for authorized binary analysis | LGPLv3 project; individual plugins can have different licenses | Optional specialist tool |
| P2 | [Frida](https://github.com/frida/frida) | Dynamic instrumentation of software | Runtime behavior analysis of software/devices you own or are authorized to test | Powerful instrumentation; isolate test targets and avoid third-party access | Optional specialist tool |
| P2 | [mitmproxy](https://github.com/mitmproxy/mitmproxy) | Inspect HTTP/TLS traffic in controlled tests | Debug our own client/proxy interactions and verify redirect/network behavior | Interception must be limited to owned/authorized test traffic; not a secure egress policy by itself | Potential lab tool, not a substitute for network controls |
| P2 | [Anthropic Agent Skills](https://github.com/anthropics/skills) and [Agent Skills standard](https://agentskills.io/) | Reusable, task-scoped instruction bundles | Borrow patterns, create vendor-neutral `SKILL.md` files for review/test/research | Skills are executable workflow guidance in natural language; inspect them like code and test triggers | Use curated patterns, don't bulk-install |

## What was actually checked in this environment

At the time of the local probe, these were available: Python `pytest` module and `requests`. These were not installed/discoverable: `semgrep`, `ast-grep`, `ruff`, `pip-audit`, `bandit`, `gitleaks`, `detect-secrets`, `promptfoo`, `deepeval`, and `langgraph`. This is a point-in-time environment observation, not a statement that the projects are unavailable or cannot be used elsewhere.

## Adoption rules

1. Do not install a tool solely because it is trending or has many stars.
2. Before adoption, record repository URL, license, release/commit recency, dependency footprint, permissions, network behavior, telemetry, and rollback procedure.
3. Run tools in an isolated worktree/copy first. No auto-fixes on the only working copy.
4. A scanner finding is not automatically a confirmed vulnerability; record evidence, false-positive rationale and severity.
5. Never put API keys, customer data, or production credentials into benchmarks or tool sandboxes.
6. No single static scanner or prompt-injection scanner proves safety. Combine deterministic tests, least privilege, network egress controls and human review.
7. Reverse-engineering tools are for owned software, authorized assessments, interoperability, debugging, malware analysis in an isolated lab, or other lawful use; not for credential theft, unauthorized access, or bypassing protections on third-party systems.

## Proposed rollout

### Stage A — zero-cost, no new dependency
- Run the existing regression/reference suites.
- Generate a local tooling inventory with `python -m agent_team.tooling_audit`.
- Keep benchmark tasks and results separate: deterministic local checks vs live-model tasks marked `not_run`.
- Add skill files as workflow guidance only; do not treat them as installed executable plugins.

### Stage B — security scanners, opt-in
- In a disposable branch, run Gitleaks and Semgrep locally.
- Run `pip-audit` only when network use is permitted; preserve the timestamp and advisory source in the report.
- Review the MCP/skills inventory with MCP-Scan only after reading its data-sharing/opt-out behavior.

### Stage C — fair agent comparison
- Use the same 12 tasks, same repository snapshot, same timeouts, same tools, same model/provider and same permissions.
- Run baseline first, then one candidate (Promptfoo as evaluation harness; OpenHands or LangGraph only if they test a specific architectural hypothesis).
- Measure task correctness, source quality, security failures, duration, estimated cost, tool calls and human intervention. Run repeats for non-deterministic tasks.
- Do not publish a winner if model/provider conditions differ or live tasks were skipped.

## Sources consulted
- Promptfoo official repository: https://github.com/promptfoo/promptfoo
- Promptfoo coding-agent evaluation guide: https://github.com/promptfoo/promptfoo/blob/main/site/docs/guides/evaluate-coding-agents.md
- DeepEval docs: https://deepeval.com/docs/introduction
- Semgrep repository: https://github.com/semgrep/semgrep
- ast-grep repository: https://github.com/ast-grep/ast-grep
- MCP Inspector: https://github.com/modelcontextprotocol/inspector
- MCP-Scan repository/docs: https://github.com/iflow-mcp/invariantlabs-ai-mcp-scan and https://github.com/invariantlabs-ai/docs/blob/main/docs/mcp-scan/index.md
- Gitleaks: https://github.com/gitleaks/gitleaks
- pip-audit: https://github.com/pypa/pip-audit
- Ghidra: https://github.com/NationalSecurityAgency/ghidra
- radare2: https://github.com/radareorg/radare2
- Frida: https://github.com/frida/frida
- mitmproxy: https://github.com/mitmproxy/mitmproxy
- Agent Skills examples: https://github.com/anthropics/skills and https://agentskills.io/

## Addendum: Anthropic + Google projects (reviewed 2026-10-23)

These are role-specific candidates, not an instruction to install everything.

| Project | Open-source role | Value to this repository | Cost/privacy boundary | Decision |
|---|---|---|---|---|
| [Anthropic Agent Skills](https://github.com/anthropics/skills) + [Agent Skills specification](https://agentskills.io/) | Reusable folder-based instruction bundles and a portable format | Adopt the format pattern; lint required metadata; keep project-specific skills versioned in-repo | A `SKILL.md` can still contain unsafe instructions; inspect as code and do not bulk-import | Adopt compatible subset; validate locally |
| [Claude Code](https://github.com/anthropics/claude-code) | Agentic coding tool and plugin ecosystem | Optional coding-workflow candidate for a separate disposable worktree | Tool availability, model access, account terms and data handling are distinct from repository license; review before use | Not installed; no account/API assumed |
| [Google Gemini CLI](https://github.com/google-gemini/gemini-cli) | Open-source terminal coding/research agent; repository documents a free quota for eligible personal accounts | Optional second coding agent to run the same code archaeology and test tasks | Free quotas and model/service terms can change; prompts/code may be sent to hosted services; shell/file/network permissions need review | Candidate for later controlled comparison |
| [Google ADK for Python](https://github.com/google/adk-python) | Open-source agent orchestration framework with workflows, tools and human approval patterns | Architectural comparison if the current router becomes a real bottleneck | Adds dependencies and framework surface; a model-agnostic claim does not make every provider free | Compare only; no integration yet |
| [Google OSS-Fuzz](https://github.com/google/oss-fuzz) | Continuous fuzzing infrastructure for open-source software | Learn fuzzing patterns; use local property/fuzz tests for parsers and URL validation first | Full integration is likely disproportionate for this small Python starter; hosted infrastructure is not assumed free or enabled | Apply lightweight local tests first |
| [Google OSV-Scanner](https://github.com/google/osv-scanner) | Dependency vulnerability scanning against OSV advisories | Complement `pip-audit` when dependencies grow or lockfiles are added | Vulnerability database freshness generally requires network access; scan is not a substitute for dependency pinning | Candidate; not run |

### New local capability

`python -m agent_team.skill_lint .` checks the required `name`/`description` metadata and folder-name match for the project's `skills/*/SKILL.md` files. It is an offline, conservative subset validator—not a full Agent Skills specification implementation and not a safety certification. It was added with unit tests. Three skills were added: prompt-injection defense, fair agent-framework evaluation, and Google agent-stack assessment.

### Decision gate

Do not add Gemini CLI, Claude Code, Google ADK, Promptfoo, or scanners to the runtime dependency list merely to benefit from their existence. Keep development tools separate from runtime dependencies; first test whether their use is possible within the user's account, quota, privacy, and permission constraints, then compare on the same benchmark.
