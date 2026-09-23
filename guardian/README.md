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

## CI and production

`.github/workflows/portfolio-ci.yml` runs TypeScript validation, the production build, repository path checks, Playwright, axe, production smoke checks, and Lighthouse. Production checks run after a successful deployment status, on the daily schedule, or through manual dispatch when `PORTFOLIO_URL` is configured.

The Vercel GitHub integration must publish deployment statuses for the post-deployment job to run automatically. Manual dispatch remains available as a fallback.

## Adding a project

1. Add the project page and its source reference to the portfolio.
2. Add one entry to `guardian/project-links.json` with its exact path in `KN-Vignesh/Projects`.
3. Add or update the corresponding browser project configuration in `tests/e2e/project-config.ts`.
4. Run the Guardian checks locally before opening a pull request.

Do not add speculative paths. A moved or deleted project should fail the repository check until its portfolio reference is updated.

## Future AI diagnosis

The deterministic checks are intentionally separate from AI. A future diagnosis job can consume the JSON reports, browser traces, screenshots, and workflow metadata, then create a GitHub Issue or a repair proposal. It must create a branch and pull request for changes; it must never edit `main` directly or receive unrestricted access to secrets and workflow permissions.
