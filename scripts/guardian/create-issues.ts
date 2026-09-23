import { access, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { makeFingerprint, upsertGuardianIssue } from '../../guardian/issues.js';

interface FailureEvidence {
  type: string;
  check: string;
  affectedUrl?: string;
  error: string;
  evidence?: string[];
  severity?: string;
}

const evidencePath = process.env.GUARDIAN_FAILURE_FILE ?? 'guardian/failure.json';
const token = process.env.GITHUB_TOKEN;
const repository = process.env.GITHUB_REPOSITORY;
const config = JSON.parse(await readFile('guardian/config.json', 'utf8')) as { issueMode?: string };

if (config.issueMode !== 'active') {
  console.log('Guardian issue creation is not active; no GitHub write was attempted.');
  process.exit(0);
}

if (!token || !repository) {
  console.error('GITHUB_TOKEN and GITHUB_REPOSITORY are required to create Guardian issues.');
  process.exit(2);
}

async function loadFailures(): Promise<FailureEvidence[]> {
  try {
    await access(evidencePath);
    return JSON.parse(await readFile(evidencePath, 'utf8')) as FailureEvidence[];
  } catch {
    const failures: FailureEvidence[] = [];
    for (const [file, type, check] of [
      ['links.json', 'broken-link', 'Portfolio link scan'],
      ['code-repository.json', 'project-reference', 'GitHub project reference scan'],
    ] as const) {
      try {
        const report = JSON.parse(await readFile(path.join('guardian', 'reports', file), 'utf8')) as { checks?: Array<{ healthy: boolean; target?: string; path?: string; message: string }> };
        for (const item of report.checks ?? []) {
          if (!item.healthy) failures.push({
            type,
            check,
            affectedUrl: item.target ?? item.path,
            error: item.message,
            evidence: [`Report: guardian/reports/${file}`],
            severity: 'medium',
          });
        }
      } catch {
        // Missing reports are handled by the health workflow itself.
      }
    }
    if (failures.length === 0) {
      try {
        const report = JSON.parse(await readFile(path.join('guardian', 'reports', 'guardian-report.json'), 'utf8')) as { status?: string; checks?: Record<string, string> };
        if (report.status === 'failed') {
          for (const [check, status] of Object.entries(report.checks ?? {})) {
            if (status === 'failed') failures.push({
              type: check === 'productionSmoke' ? 'production' : check === 'projectReferences' ? 'project-reference' : 'bug',
              check: `Guardian ${check}`,
              error: `${check} check failed.`,
              evidence: ['Report: guardian/reports/guardian-report.json'],
              severity: check === 'productionSmoke' ? 'high' : 'medium',
            });
          }
        }
      } catch {
        // A missing unified report leaves no issue evidence to publish.
      }
    }
    return failures;
  }
}

const failures = await loadFailures();
const issueResults: Array<{ fingerprint: string; issueNumber: number; issueUrl: string; failure: FailureEvidence }> = [];
for (const failure of failures) {
  const issueType = ['bug', 'broken-link', 'accessibility', 'performance', 'security', 'production', 'project-reference', 'ai-diagnosis'].includes(failure.type)
    ? failure.type
    : 'bug';
  const fingerprint = makeFingerprint([failure.type, failure.check, failure.affectedUrl ?? 'unknown-route', failure.error]);
  const result = await upsertGuardianIssue({
    repository,
    token,
    title: `[Portfolio Guardian] ${failure.error}`,
    fingerprint,
    severity: failure.severity ?? 'medium',
    check: failure.check,
    affectedUrl: failure.affectedUrl,
    error: failure.error,
    evidence: failure.evidence ?? [],
    labels: ['guardian', `guardian:${issueType}`, 'guardian:needs-review'],
  });
  issueResults.push({ fingerprint, issueNumber: result.number, issueUrl: result.url, failure });
  console.log(`${result.created ? 'Created' : 'Updated'} Guardian issue #${result.number}: ${result.url}`);
}
if (failures.length === 0) console.log('No blocking Guardian failures found; no GitHub Issue was created.');
await mkdir(path.join('guardian', 'reports'), { recursive: true });
await writeFile('guardian/reports/issue-results.json', `${JSON.stringify({ generatedAt: new Date().toISOString(), issues: issueResults }, null, 2)}\n`);
