# Scheduled maintenance and multi-agent execution

## Provider-free maintenance

The [scheduled offline maintenance workflow](../.github/workflows/scheduled-offline-maintenance.yml) runs weekly and does not call hosted AI providers. It produces test and readiness reports for review.

## Scheduled multi-agent tasks (disabled by default)

The [scheduled multi-agent workflow](../.github/workflows/scheduled-agent-task.yml) is scheduled for Tuesdays at 09:37 UTC. It skips the task unless the repository variable `ENABLE_SCHEDULED_AGENT_RUN` is exactly `true` and `SCHEDULED_AGENT_TASK` is non-empty.

Before enabling live scheduled execution:

1. Add repository Actions secret `OPENROUTER_API_KEY` in Settings → Secrets and variables → Actions → Secrets.
2. Add repository Actions variable `SCHEDULED_AGENT_TASK` containing the recurring task. Treat this variable as visible to repository maintainers; do not put private or sensitive data in it. The task is limited to 5,000 characters.
3. Only after you explicitly authorize recurring provider calls, add repository Actions variable `ENABLE_SCHEDULED_AGENT_RUN` with value `true`.

If the opt-in variable is absent or not `true`, the scheduled multi-agent job is skipped and no provider request is made. If the API secret is missing, the job exits before invoking the team. When enabled, the planner, executor, reviewer, and final revision stage use the configured free-first OpenRouter route; free-model availability is not guaranteed, and provider limits may still apply.

Successful output is uploaded as an artifact retained for one day. The workflow does not commit generated output or modify repository files. Review results manually before using them.

## Links

- [Actions secrets settings](https://github.com/ghith93/agent-team-starter/settings/secrets/actions)
- [Actions variables settings](https://github.com/ghith93/agent-team-starter/settings/variables/actions)
- [Manual one-off agent task](../.github/workflows/on-demand-agent-task.yml)
