# Technical design

The frontend is React 19 with Vite, TypeScript, Tailwind CSS, Lucide icons, and Motion. The backend uses Express and lightweight TypeScript modules rather than a large GitHub SDK. GitHub data is fetched only for the pull request and its changed files.

The analysis pipeline is intentionally ordered:

1. **Ingestion** parses the URL and retrieves the smallest useful GitHub payload.
2. **Static analysis** runs deterministic rules locally and creates SonarQube-shaped metrics and issues.
3. **Jev inference** supplies structured probabilistic decisions, with deterministic fallback behavior in the engine.
4. **Decision policy** converts evidence into an auditable verdict.

This separation keeps model output from directly approving or blocking a change. The final decision remains inspectable TypeScript policy code.

## Limits

The anonymous trial store is process-local, so it resets when the server restarts and is not suitable for a multi-instance quota without shared storage. Public GitHub access is subject to API rate limits. Live Jev analysis depends on the configured provider key; the local application remains useful with its deterministic analysis and fixtures.