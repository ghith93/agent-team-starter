# Access Boundaries and Side-Effect Gates
Status: required operating policy for integrations.

## Separate authorization domains
GitHub access does not imply access to Meta Business Manager, Facebook Pages, Instagram accounts, customer inboxes, ad accounts, billing, or deployment infrastructure. Every service requires its own authenticated connection and asset-level permissions.

## Safe initial mode
- GitHub: work on feature branches and use pull requests.
- Meta Ads: read-only access first; no budget or campaign mutation.
- Social publishing: create drafts/previews only; no public publishing during setup.
- CRM/inbox: use synthetic records; do not send messages to real customers during tests.
- Providers/models: offline tests first; check quotas and billing before any live inference.
- Deployment: no secrets committed to the repository.

## Secret handling
- Never paste access tokens, app secrets, cookies, recovery codes, or private keys into chat.
- Use an appropriate secret manager, GitHub Actions secrets, or local environment variables in the deployment environment.
- Use the least-privilege token that supports the exact task, with an expiry where possible.
- Redact tokens and sensitive customer data from logs and issue reports.
- Rotate any credential that may have been exposed.

## Human approval gates
Explicit approval is required before:
- Publishing or scheduling public content.
- Creating/reactivating campaigns or ads.
- Changing budgets, bids, audiences or campaign status.
- Sending outbound customer messages.
- Exporting customer lists or uploading them to ad platforms.
- Making purchases, enabling paid services, or deploying public endpoints.
- Deleting data or changing account-wide security settings.

## Audit requirements
For every future side-effecting action record: who/what requested it, target account/asset, proposed change, preview, approval, timestamp, result, rollback path, and evidence. If target identity or permission is uncertain, fail closed.
