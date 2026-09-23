# Guardian Security Audit

Last reviewed: 2026-09-23

| Workflow or module | Contents | Issues | Pull requests | Secrets | Current purpose |
| --- | --- | --- | --- | --- | --- |
| `portfolio-ci.yml` | read | none | none | none | Deterministic health checks |
| `guardian-dry-run.yml` | read | none | none | none | Simulated pipeline artifacts |
| `scripts/guardian/create-issues.ts` | API caller only | requires caller permission | none | `GITHUB_TOKEN` when explicitly invoked | Issue helper, not connected to CI |
| `scripts/guardian/diagnose-failure.ts` | no repository write | none | none | `AI_API_KEY` when explicitly invoked | Structured diagnosis helper |
| `guardian/vercel/status.ts` | none | none | none | none | Explicitly disabled Vercel adapter |

## Current safety state

- Automation mode is `dry-run`.
- Normal health workflows use `contents: read`.
- No workflow has `contents: write`, `issues: write`, or `pull-requests: write`.
- No Guardian code pushes to `main`, creates branches, creates PRs, merges, calls Vercel mutation APIs, or rolls back deployments.
- AI output is schema-validated before policy evaluation.
- Protected paths are defined in `guardian/policies/automation-policy.json`.
- `autoMerge` and `rollback` are disabled.

## Manual controls still required

Configure branch protection for `main`, require pull requests and Guardian status checks, prevent force pushes, and review any future write-capable workflow separately. Do not add write permissions to the read-only health workflow.
