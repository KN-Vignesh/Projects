import type { Diagnosis } from './ai/types.js';
import { evaluateAutoFixPolicy } from './ai/policy.js';
import { validateRepairPlan, type RepairPlanItem } from './ai/repair-plan.js';
import { makeFingerprint } from './issues.js';

export interface DryRunArtifacts {
  failure: {
    type: string;
    check: string;
    affectedUrl: string;
    error: string;
    severity: string;
    evidence: string[];
  };
  fingerprint: string;
  diagnosis: Diagnosis;
  policy: { allowed: boolean; reasons: string[] };
  issuePreview: string;
  repairPlan: RepairPlanItem[];
  repairValidation: { valid: boolean; reasons: string[] };
  branchPreview: { wouldCreateBranch: boolean; branchName: string; baseBranch: string; baseCommit: string | null; riskLevel: string };
  prPreview: string;
}

export async function buildDryRunArtifacts(): Promise<DryRunArtifacts> {
  const failure = {
    type: 'broken-link',
    check: 'synthetic Guardian failure',
    affectedUrl: '#/projects/customer-churn',
    error: 'Synthetic 404 used to verify the dry-run pipeline.',
    severity: 'low',
    evidence: ['Synthetic failure; no production request was made.'],
  };
  const fingerprint = makeFingerprint([failure.type, failure.affectedUrl, '404']);
  const diagnosis: Diagnosis = {
    problem: failure.error,
    rootCause: 'Synthetic evidence represents a stale project route.',
    confidence: 0.91,
    affectedFiles: ['README.md'],
    affectedRoutes: [failure.affectedUrl],
    evidence: failure.evidence,
    proposedFix: 'Replace the stale route with the validated project route.',
    repairPlan: ['Update the project route and rerun deterministic validation.'],
    riskLevel: 'low',
    autoFixAllowed: true,
    requiresHumanReview: true,
  };
  const policy = await evaluateAutoFixPolicy(diagnosis);
  const issuePreview = [
    '# Guardian Issue Preview',
    '',
    '## Action',
    '',
    'WOULD CREATE ISSUE',
    '',
    `## Fingerprint\n\n\`${fingerprint}\``,
    '',
    '## Labels',
    '',
    '- guardian',
    '- guardian:broken-link',
    '- guardian:needs-review',
    '',
    `## Severity\n\n${failure.severity}`,
    '',
    '## Evidence',
    '',
    ...failure.evidence.map((item) => `- ${item}`),
    '',
    'DRY RUN - NO GITHUB ISSUE CREATED',
    '',
  ].join('\n');
  const repairPlan: RepairPlanItem[] = [{
    file: diagnosis.affectedFiles[0],
    action: 'update',
    reason: 'The route is represented as stale by the synthetic failure.',
    change: diagnosis.proposedFix,
  }];
  const repairValidation = await validateRepairPlan(repairPlan);
  const branchName = `guardian/fix-${failure.type}`;
  const branchPreview = {
    wouldCreateBranch: true,
    branchName,
    baseBranch: 'main',
    baseCommit: process.env.GITHUB_SHA ?? null,
    riskLevel: diagnosis.riskLevel,
  };
  const prPreview = [
    `# [Guardian] Fix ${failure.type}`,
    '',
    '## Status',
    '',
    'DRY RUN - PR NOT CREATED',
    '',
    `## Branch\n\n\`${branchName}\``,
    '',
    `## Problem\n\n${diagnosis.problem}`,
    '',
    `## Root Cause\n\n${diagnosis.rootCause}`,
    '',
    '## Proposed Fix',
    '',
    ...repairPlan.map((item) => `- ${item.file}: ${item.change}`),
    '',
    `## Risk\n\n${diagnosis.riskLevel}`,
    '',
    '## Validation',
    '',
    '- TypeScript',
    '- Build',
    '- Playwright',
    '- Accessibility',
    '- Lighthouse',
    '- Link scan',
    '- Project validation',
    '',
  ].join('\n');
  return { failure, fingerprint, diagnosis, policy, issuePreview, repairPlan, repairValidation, branchPreview, prPreview };
}
