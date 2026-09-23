import { readFile } from 'node:fs/promises';
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

if (!token || !repository) {
  console.error('GITHUB_TOKEN and GITHUB_REPOSITORY are required to create Guardian issues.');
  process.exit(2);
}

const failure = JSON.parse(await readFile(evidencePath, 'utf8')) as FailureEvidence;
const issueType = ['bug', 'broken-link', 'accessibility', 'performance', 'security', 'production', 'project-reference', 'ai-diagnosis'].includes(failure.type)
  ? failure.type
  : 'bug';
const fingerprint = makeFingerprint([
  failure.type,
  failure.check,
  failure.affectedUrl ?? 'unknown-route',
  failure.error,
]);
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
console.log(`${result.created ? 'Created' : 'Updated'} Guardian issue #${result.number}: ${result.url}`);
