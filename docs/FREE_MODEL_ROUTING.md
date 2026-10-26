# Role-specific free model routing

The router supports separate, validated free-model pools for each stage:

- `OPENROUTER_PLAN_MODELS`
- `OPENROUTER_DRAFT_MODELS`
- `OPENROUTER_REVIEW_MODELS`
- `OPENROUTER_REVISE_MODELS`

Each value is a comma-separated list of OpenRouter model IDs. Every ID must be exactly `openrouter/free` or end in `:free`; paid IDs are rejected before any provider call. When a stage-specific variable is absent, that stage inherits `OPENROUTER_FREE_MODELS`. The router tries each configured ID in order and never adds a paid fallback.

## Current workflow defaults

The repository's manually authorized and scheduled agent workflows now use:

- Planner and reviewer: `nvidia/nemotron-3-ultra-550b-a55b:free`, then `openrouter/free`.
- Draft/code generation: `cohere/north-mini-code:free`, then `openrouter/free`.
- Final revision: the shared `openrouter/free` pool unless `OPENROUTER_REVISE_MODELS` is configured.
- Repository patch proposal: `cohere/north-mini-code:free`, then `openrouter/free`.

These are role-based starting candidates, not a claim that they always win on this repository's benchmark. The public OpenRouter catalog lists North Mini Code as a free, coding-focused model with a 256K context window and lists Nemotron 3 Ultra as a free reasoning/orchestration model with a 1M context window. Availability and rate limits can change; the fallback alias remains free-only. See [North Mini Code (free)](https://openrouter.ai/cohere/north-mini-code:free), [Nemotron 3 Ultra (free)](https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b:free), and [OpenRouter's free model collection](https://openrouter.ai/collections/free-models).

## Privacy and evaluation

- Free endpoints may log or retain prompts according to provider terms. NVIDIA's Nemotron free endpoint explicitly warns against sending confidential information or personal data. The on-demand workflow therefore labels its task input as non-sensitive; do not enable live tasks containing secrets or private customer data.
- A `:free` identifier and the `openrouter/free` alias do not guarantee uptime or unlimited quota. Rate limits can cause the router to move to the next configured free ID.
- The `openrouter/free` alias can select a free model dynamically. OpenRouter's collection ranking is based on usage, not proof of code quality.
- Compare role-specific pools against the same offline benchmark and acceptance tests before claiming quality gains. No model call is required to change or validate routing configuration.
