import assert from 'node:assert/strict';
import test from 'node:test';
import { validateDiagnosis } from '../../guardian/ai/validator.js';
import { evaluateAutoFixPolicy } from '../../guardian/ai/policy.js';
import { findIssueByFingerprint, makeFingerprint, issueBody } from '../../guardian/issues.js';
import { validateRepairPlan } from '../../guardian/ai/repair-plan.js';

const validDiagnosis = {
  problem: 'A project route is broken.',
  rootCause: 'The route references a stale path.',
  confidence: 0.92,
  affectedFiles: ['README.md'],
  affectedRoutes: ['#/projects/example'],
  evidence: ['The browser received HTTP 404.'],
  proposedFix: 'Update the route to the validated project path.',
  repairPlan: ['Update the route reference.'],
  riskLevel: 'low' as const,
  autoFixAllowed: true,
  requiresHumanReview: true,
};

test('diagnosis validation accepts the documented schema', () => {
  assert.deepEqual(validateDiagnosis(validDiagnosis), validDiagnosis);
});

test('diagnosis validation rejects unsafe risk declarations', () => {
  assert.throws(() => validateDiagnosis({ ...validDiagnosis, riskLevel: 'high', autoFixAllowed: true }));
  assert.throws(() => validateDiagnosis({ ...validDiagnosis, confidence: 2 }));
  assert.throws(() => validateDiagnosis({ ...validDiagnosis, unexpected: true }));
});

test('policy blocks protected files and allows only low-risk reviewed repairs', async () => {
  const allowed = await evaluateAutoFixPolicy(validDiagnosis);
  assert.equal(allowed.allowed, true);

  const protectedFile = await evaluateAutoFixPolicy({ ...validDiagnosis, affectedFiles: ['.github/workflows/portfolio-ci.yml'] });
  assert.equal(protectedFile.allowed, false);
  assert.match(protectedFile.reasons.join(' '), /Protected path/);
});

test('issue fingerprints and machine-readable markers are stable', () => {
  const fingerprint = makeFingerprint(['Playwright', '/projects/example', '404']);
  assert.equal(fingerprint, 'playwright:/projects/example:404');
  assert.match(issueBody({
    fingerprint,
    severity: 'medium',
    check: 'Playwright navigation',
    error: '404',
    evidence: ['response status 404'],
  }), /guardian-fingerprint:\nplaywright:\/projects\/example:404/);
});

test('issue deduplication maps the same fingerprint to one issue', () => {
  const fingerprint = 'playwright:/projects/example:404';
  const issues = [
    { number: 12, html_url: 'https://github.com/example/issues/12', body: issueBody({ fingerprint, severity: 'medium', check: 'Playwright', error: '404', evidence: [] }) },
  ];
  assert.equal(findIssueByFingerprint(issues, fingerprint)?.number, 12);
  assert.equal(findIssueByFingerprint(issues, 'playwright:/projects/other:404'), undefined);
});

test('repair plans require real unprotected update targets', async () => {
  const valid = await validateRepairPlan([{ file: 'README.md', action: 'update', reason: 'test', change: 'test' }]);
  assert.equal(valid.valid, true);
  const protectedPlan = await validateRepairPlan([{ file: '.github/workflows/portfolio-ci.yml', action: 'update', reason: 'test', change: 'test' }]);
  assert.equal(protectedPlan.valid, false);
});