---
name: google-agent-stack
description: Assess Google open-source agent tooling such as Gemini CLI, Google ADK, and OSS-Fuzz for a project without assuming API access or installing dependencies.
---

# Google Agent Stack Assessment

1. Distinguish the open-source license of a CLI/framework from the commercial terms, quotas, data handling, and eligibility of the model or hosted service it connects to.
2. Inspect the official repository, license, supported runtime, release notes, security policy, telemetry, permissions, and minimum dependency footprint.
3. For Gemini CLI, evaluate local code-navigation and test-writing workflows on a disposable repository; do not provide production secrets or approve shell/file/network actions blindly.
4. For Google ADK, map only the concrete workflow requirements that exceed the current router. Prototype behind an adapter rather than rewriting the baseline first.
5. For OSS-Fuzz, determine whether the target language and project setup are suitable; use local fuzz/property tests for small Python parsers when a full OSS-Fuzz integration is disproportionate.
6. Record whether the task can run fully offline, needs a Google account, consumes a quota, transmits code, or requires deployment credentials.
7. Run the same benchmark against the baseline. Preserve the baseline and remove the prototype cleanly if the expected benefit is not demonstrated.
