# VERO

## AI code analysis for pull requests

VERO is an evidence-based GitHub pull request analysis application. It combines real pull request metadata and patches with deterministic static checks, structured TypeSafe Jev signals, and explicit policy rules.

The product principle is simple: **code computes, static analysis detects, Jev decides, and policy code makes the verdict.** The application can inspect public pull requests without requiring a repository checkout, then presents the evidence behind its recommendation.

<div class="vp-tags"><span>GITHUB PR INGESTION</span><span>SONARQUBE-STYLE RULES</span><span>TYPESAFE JEV</span><span>DETERMINISTIC POLICY</span></div>

<p><a class="vp-hero-actions" href="/vero/">LAUNCH VERO ↗</a></p>

## What it does

- Fetches pull request metadata and changed-file patches from GitHub.
- Runs local deterministic checks for vulnerabilities, bugs, code smells, complexity, and test signals.
- Produces typed Jev classifications and calibrated risk signals when the configured provider is available.
- Applies auditable decision rules to produce a final verdict, evidence trail, and review guidance.
- Shows the diff, findings, telemetry, evaluation data, and a copyable Markdown report in one interface.

## Documentation

- [Architecture](architecture.md)
- [Features](features.md)
- [Technical design](technical-design.md)
- [Deployment](deployment.md)

## Configuration

The server accepts optional `GITHUB_TOKEN` and `TYPESAFE_API_KEY` values for higher GitHub API limits and live Jev inference. Users can also provide their own keys through the application settings dialog. See [deployment](deployment.md) for the complete environment-variable model.