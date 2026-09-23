# Guardian Security Audit

Last reviewed: 2026-09-23

| Workflow or module | Contents | Issues | Pull requests | Secrets | Current purpose |
| --- | --- | --- | --- | --- | --- |
| `portfolio-ci.yml` | read | none | none | none | Deterministic health checks |
| `guardian-dry-run.yml` | read | none | none | none | Simulated pipeline artifacts |
| `guardian-issues.yml` | read | write | none | `GITHUB_TOKEN` | Issue-only activation after failed Guardian run |
| `guardian-issue-integration-test.yml` | read | write | none | `GITHUB_TOKEN` | Explicitly confirmed create/deduplicate/close test |
| `guardian-ai-diagnosis.yml` | read | write comments | none | `GITHUB_TOKEN`, `AI_API_KEY` | Validated diagnosis comments only |
| `guardian/repair/executor.ts` | no workflow access | none | none | none | Exact-operation repair executor, disabled by config and active gate |
| `guardian/repair/branch.ts` | no workflow access | none | none | none | Deterministic branch preview/planner only |
| `guardian/repair/pr.ts` | no workflow access | none | none | none | PR preview/planner only; auto-merge rejected |
| `scripts/guardian/create-issues.ts` | API caller only | requires caller permission | none | `GITHUB_TOKEN` when explicitly invoked | Deduplicated issue creation/update |
| `scripts/guardian/diagnose-failure.ts` | no repository write | none | none | `AI_API_KEY` when explicitly invoked | Structured diagnosis helper |
| `guardian/vercel/status.ts` | none | none | none | none | Explicitly disabled Vercel adapter |

## Current safety state

- Source automation mode is `dry-run`; issue and diagnosis stages are separately activated.
- Normal health workflows use `contents: read`.
- `guardian-issues.yml` and `guardian-ai-diagnosis.yml` have `issues: write`; no workflow has `contents: write` or `pull-requests: write`.
- No Guardian code pushes to `main`, creates branches, creates PRs, merges, calls Vercel mutation APIs, or rolls back deployments.
- AI output is schema-validated before policy evaluation.
- AI diagnosis can only comment on an existing Issue; it cannot modify source or create branches.
- `repairMode` and `prMode` are `disabled`.
- `GUARDIAN_ACTIVE_AUTOMATION` is not enabled.
- Repair operations are finite exact replacements; arbitrary shell commands are not accepted.
- Repair plans require low risk, configured confidence, real paths, unprotected files, and known operation types.
- Protected paths are defined in `guardian/policies/automation-policy.json`.
- `autoMerge` and `rollback` are disabled.

## Manual controls still required

Configure branch protection for `main`, require pull requests and Guardian status checks, prevent force pushes, and review any future write-capable workflow separately. Do not add write permissions to the read-only health workflow.
