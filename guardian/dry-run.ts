import type { Diagnosis } from './ai/types.js';
import { evaluateAutoFixPolicy } from './ai/policy.js';
import { validateRepairPlan, type RepairPlanItem } from './ai/repair-plan.js';
import { executeRepairPlan } from './repair/executor.js';
import { planRepairBranch, type BranchPreview } from './repair/branch.js';
import { buildPullRequestPreview } from './repair/pr.js';
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
  branchPreview: BranchPreview;
  prPreview: string;
  repairExecution: { status: string; reason: string; filesChanged: string[]; operationsApplied: number };
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
    affectedFiles: ['projects/customer-churn.md'],
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
  const structuredPlan = {
    repairId: `repair-${fingerprint.replace(/[^a-z0-9]+/gi, '-')}`,
    fingerprint,
    riskLevel: 'low' as const,
    confidence: diagnosis.confidence,
    operations: [{
      type: 'update_route_reference' as const,
      file: 'projects/customer-churn.md',
      oldValue: '#/projects/old-customer-churn',
      newValue: '#/projects/customer-churn',
    }],
    reason: diagnosis.proposedFix,
    expectedValidation: ['typescript', 'build', 'playwright', 'links'],
  };
  const repairExecution = await executeRepairPlan(structuredPlan, {
    mode: 'dry-run',
    repairMode: 'disabled',
    automation: { sourceModification: false },
  }, 'main');
  const branchPreview = planRepairBranch(fingerprint, { mode: 'dry-run', repairMode: 'disabled', baseBranch: 'main' }, process.env.GITHUB_SHA ?? null);
  const prPreview = buildPullRequestPreview({
    fingerprint,
    branchName: branchPreview.branchName,
    problem: diagnosis.problem,
    rootCause: diagnosis.rootCause,
    riskLevel: diagnosis.riskLevel,
    repairPlan: repairPlan.map((item) => `${item.file}: ${item.change}`),
    validation: ['TypeScript', 'Build', 'Playwright', 'Accessibility', 'Lighthouse', 'Link scan', 'Project validation'],
  });
  return { failure, fingerprint, diagnosis, policy, issuePreview, repairPlan, repairValidation, branchPreview, prPreview, repairExecution };
}
