# Ruflo pilot boundary

This folder is an integration decision record, not an installed or running Ruflo service.

- Upstream project: https://github.com/ruvnet/ruflo
- Pilot plan: [RUFLO_ADOPTION_PLAN.md](../../docs/RUFLO_ADOPTION_PLAN.md)
- This repository remains a Python-first, offline-capable workflow.
- Do not add Ruflo to the default Python requirements or production path.
- Do not use floating `@latest` versions in production; pin and review a tested version first.
- Any trial must be disposable, use synthetic data, avoid provider calls by default, and run with least privilege.
- Do not commit credentials, generated memory stores, local configuration, or runtime logs.
