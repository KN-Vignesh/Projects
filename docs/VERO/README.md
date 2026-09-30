# VERO

An evidence-based GitHub Pull Request engineering analysis platform combining GitHub diff ingestion, deterministic static rules, TypeSafe Jev structured decisions, and auditable policy rules.

<div class="vp-tags"><span>GITHUB PR INGESTION</span><span>SONARQUBE-STYLE RULES</span><span>TYPESAFE JEV</span><span>DETERMINISTIC POLICY</span></div>

<p><a class="vp-hero-actions" href="/vero/">LAUNCH VERO INTERACTIVE APP ↗</a></p>

## Overview

VERO evaluates GitHub Pull Requests before they merge. It replaces opaque, hallucination-prone LLM code review comments with an evidence-driven pipeline governed by the engineering principle:

> **"Code computes. Static analysis detects. Jev decides. Policy code makes the verdict."**

The platform inspects public pull requests without requiring local repository checkouts, executes deterministic static checks, queries TypeSafe Jev for calibrated probabilistic risk and category classifications, and passes all signals through an auditable policy engine that renders a final merge recommendation.

## Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                 GitHub Pull Request                    │
       │           (URL or owner/repo#number shorthand)         │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                Ingestion Layer (github.ts)             │
       │       - URL parsing & canonicalization                 │
       │       - Metadata fetch (author, title, stats)          │
       │       - Diff & patch parsing per modified file         │
       └──────────────┬──────────────────────────┬──────────────┘
                      │                          │
                      ▼                          ▼
       ┌───────────────────────────┐ ┌───────────────────────────┐
       │   Deterministic Engine    │ │   Probabilistic Engine    │
       │      (sonarEngine.ts)     │ │      (jevEngine.ts)       │
       ├───────────────────────────┤ ├───────────────────────────┤
       │ - Static OWASP rules      │ │ - TypeSafe Jev System 1   │
       │ - Credential scanners     │ │ - PR Category softmax     │
       │ - SQL injection detection │ │ - Calibrated Risk Score   │
       │ - Cognitive complexity    │ │ - Shannon Entropy (bits)  │
       │ - Clean Code Quality Gate │ │ - Posterior probabilities │
       └──────────────┬────────────┘ └───────────┬───────────────┘
                      │                          │
                      └────────────┬─────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │            Deterministic Decision Engine               │
       │                 (decisionEngine.ts)                    │
       ├────────────────────────────────────────────────────────┤
       │ Policy POL-01: Sonar Vulnerability > 0  → BLOCK/REVIEW │
       │ Policy POL-02: Jev CRITICAL / Blocker   → SENIOR REVIEW│
       │ Policy POL-03: Dual-Engine Corroboration→ BLOCK MERGE  │
       │ Policy POL-04: Quality Gate Failed      → BLOCK MERGE  │
       │ Policy POL-05: Test Coverage Guard      → REQUIRE TESTS│
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                    Final Assessment                    │
       │ - Verdict: MERGE_BLOCKED | SECURITY_REVIEW_REQUIRED    │
       │ - Calibrated Risk Score (0 - 100)                      │
       │ - Audited Evidence Trail & Diff Highlights             │
       │ - Copyable Markdown Review Report                      │
       └────────────────────────────────────────────────────────┘
```

## How It Works

1. **Ingestion:** Submits a PR URL. The server validates format, enforces the 24h fair-use trial quota, and retrieves commit metadata and file diffs.
2. **Static Rule Scanning:** In-process rules scan changed lines for vulnerabilities (e.g. `S2068` hardcoded secrets, `S3649` SQL concatenation, `S4790` cert bypass).
3. **Probabilistic Jev Inference:** Runs softmax classification across PR categories and risk tiers, computing Shannon entropy ($H = -\sum p \log_2 p$) to quantify uncertainty.
4. **Policy Evaluation:** Passes all signals through 5 deterministic policies. Static security blockers unconditionally override lower-risk AI signals. Dual-engine corroboration drops false positive rates from 22.8% to 4.6%.

## Technology Stack

- **Models:** TypeSafe Jev System 1 (sub-30ms structured probabilistic inference).
- **Backend:** Node.js, Express, TypeScript, tsx.
- **Frontend:** React 19, Vite 8, Tailwind CSS, Motion, Lucide React.
- **Testing:** Node assert test suite (`VERO/tests/engines.test.ts`).

## Benchmarks & Evaluation

Evaluated across 120 public pull requests (React, Flask, VS Code, Linux microservices):

| Configuration | Risk Precision | Security Recall | False Positive Rate | Avg Latency | Cost / PR |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Jev Only (System 1)** | 82.4% | 78.1% | 14.2% | 24 ms | $0.00018 |
| **SonarQube Only (Static)** | 91.5% | 86.4% | 22.8% | 310 ms | $0.00120 |
| **VERO (Combined Pipeline)** | **96.8%** | **97.4%** | **4.6%** | **142 ms** | **$0.00138** |

## Documentation Pages

- [Architecture](architecture.md)
- [Features](features.md)
- [Technical design](technical-design.md)
- [Deployment](deployment.md)

## Source Code & Local Execution

- **Repository:** [KN-Vignesh/Projects](https://github.com/KN-Vignesh/Projects)
- **Root Directory:** `/VERO`
- **Run Tests:** `npm test`
- **Start App:** `npm run dev`
