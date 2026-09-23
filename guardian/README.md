# AI Portfolio Guardian

The Guardian is the deterministic reliability layer around this portfolio. It validates the build, browser behavior, accessibility, deployment, external links, and references into the `KN-Vignesh/Projects` repository.

## Configuration

- `guardian/config.json` defines repository identity, required portfolio sections, and enabled checks.
- `guardian/project-links.json` defines project paths that must continue to exist in the code repository.
- `${PORTFOLIO_URL}` is resolved by CI for production smoke tests. Set it as a GitHub Actions repository variable.
- `GITHUB_TOKEN` is optional for public repository checks, but increases GitHub API rate limits.

The current checkout is the `KN-Vignesh/Projects` repository, so both repository identifiers currently point to that repository. Update `portfolioRepository` when the portfolio is split into a separate repository.

## Local usage

```bash
npm run guardian:links
npm run guardian:repo
npm run guardian:check
```

Reports are written to `guardian/reports/` and are ignored by Git. The repository path checker uses the GitHub Contents API and does not require a checkout of the watched repository.

Generate the unified report locally with:

```bash
npm run guardian:report -- --environment=local
```

The report is also written to `guardian-report.json` and `guardian-report.md` for CI artifact collection.

## CI and production

`.github/workflows/portfolio-ci.yml` runs TypeScript validation, the production build, repository path checks, Playwright, axe, production smoke checks, and Lighthouse. Production checks run after a successful deployment status, on the daily schedule, or through manual dispatch when `PORTFOLIO_URL` is configured.

The Vercel GitHub integration must publish deployment statuses for the post-deployment job to run automatically. Manual dispatch remains available as a fallback.

## Issue automation

`guardian/issues.ts` provides deterministic fingerprints, Guardian label creation, and open-issue deduplication. `npm run guardian:issues` consumes a `GUARDIAN_FAILURE_FILE` or downloaded Guardian reports and requires `GITHUB_TOKEN` plus `GITHUB_REPOSITORY`. The isolated `guardian-issues.yml` workflow is the first real activation: it runs only after a failed Guardian workflow, has `issues: write` but no contents or pull-request write permission, and stops after creating or updating issues.

`guardian-ai-diagnosis.yml` is the Phase C handoff. It runs after successful issue activation, consumes `issue-results.json`, calls the configured provider, validates the response, and comments the diagnosis on the existing Issue. It has no source, branch, pull-request, merge, Vercel, or rollback capability.

## Controlled repair boundary

The repair layer currently provides only schema validation, finite operation validation, exact-replacement execution code, deterministic branch planning, PR previews, and dry-run artifacts. Configuration remains:

```text
mode = dry-run
repairMode = disabled
prMode = disabled
autoMerge = false
vercelApi = false
rollback = false
```

Real repair additionally requires `mode=active`, `repairMode=active`, `GUARDIAN_ACTIVE_AUTOMATION=true`, a non-`main` branch, a low-risk validated plan, and successful deterministic validation. No workflow enables those gates. Branch creation and PR creation are planners only, and human review remains the final boundary.

To test the real GitHub artifact and permission path, manually dispatch `guardian-issue-integration-test.yml` with the exact confirmation value `CREATE_AND_CLOSE_TEST_ISSUE`. It creates a synthetic Issue, verifies its fingerprint and labels, reruns the same failure to verify deduplication, then closes the test Issue. This workflow is not scheduled.

## Dry-run pipeline

Run the complete contained demonstration with:

```bash
npm run guardian:dry-run
npm run guardian:report -- --environment=dry-run
npm run guardian:evidence
```

The synthetic failure produces an evidence manifest, issue preview, AI diagnosis preview, validated repair plan, branch preview, and pull-request preview. Every preview says what *would* happen, but no GitHub Issue, branch, source edit, push, PR, Vercel call, or rollback occurs. Running it repeatedly produces the same failure fingerprint.

The manual [`guardian-dry-run.yml`](../.github/workflows/guardian-dry-run.yml) workflow accepts `dry-run`, `observe`, and `active` as displayed choices, but only `dry-run` is enabled. The other choices fail before any automation step.

## Adding a project

1. Add the project page and its source reference to the portfolio.
2. Add one entry to `guardian/project-links.json` with its exact path in `KN-Vignesh/Projects`.
3. Add or update the corresponding browser project configuration in `tests/e2e/project-config.ts`.
4. Run the Guardian checks locally before opening a pull request.

Do not add speculative paths. A moved or deleted project should fail the repository check until its portfolio reference is updated.

## AI diagnosis and safety

The provider-neutral diagnosis path is available through `npm run guardian:diagnose` when `AI_API_KEY`, `AI_MODEL`, `AI_BASE_URL` (optional), and `GUARDIAN_FAILURE_FILE` are configured. The response is parsed and validated against `guardian/ai/types.ts`; malformed or unsafe output stops the pipeline.

`guardian/policies/automation-policy.json` currently permits only low-risk, human-reviewed repairs and blocks protected paths such as workflows, environment files, lockfiles, deployment configuration, and server entrypoints. Phase C diagnosis is comment-only. Source modification, branch creation, pull-request creation, merge, rollback, and Vercel mutation remain disabled. Guardian never pushes directly to `main` and never auto-merges.

## Required credentials

- GitHub Actions variable: `PORTFOLIO_URL`.
- GitHub Actions secret: `GITHUB_TOKEN` for issue or repository API operations. The standard Actions token is sufficient for read-only repository checks.
- Optional future diagnosis secret: `AI_API_KEY`.
- Optional future diagnosis variable: `AI_MODEL` and `AI_BASE_URL`.

`AI_API_KEY` is a GitHub Actions secret. `AI_MODEL` and `AI_BASE_URL` are GitHub Actions variables. Diagnosis receives sanitized evidence only; credentials are never included in evidence artifacts or prompts.

Do not commit `.env` files or place credentials in JSON configuration.
