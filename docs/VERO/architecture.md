# Architecture

VERO is a small React/Vite client served by an Express process. The same process exposes the analysis API and serves the portfolio at the repository root.

```text
Browser
  ├── /                 Docsify portfolio and documentation
  └── /vero/            VERO React application
                          │
                          └── /api/*
                              Express API
                              ├── GitHub ingestion
                              ├── deterministic static analysis
                              ├── TypeSafe Jev inference
                              └── decision engine
```

The client keeps browser history and user-provided keys in local storage. The server keeps the anonymous trial session in memory and never requires those keys to be committed to the repository.

## Request flow

1. The client sends a public pull request URL and session headers to `POST /api/analyze-pr`.
2. The server parses the URL and fetches metadata plus changed files.
3. Local SonarQube-style rules inspect the patch deterministically.
4. Jev produces typed category, risk, security, and review signals.
5. The decision engine combines those signals with explicit policy rules.
6. The client renders the verdict, evidence, diff annotations, and telemetry.