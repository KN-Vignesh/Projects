export interface PullRequestPreviewInput {
  fingerprint: string;
  branchName: string;
  problem: string;
  rootCause: string;
  riskLevel: string;
  repairPlan: string[];
  validation: string[];
  issueNumber?: number;
}

export function buildPullRequestPreview(input: PullRequestPreviewInput): string {
  return [
    `# [Guardian] Repair ${input.fingerprint}`,
    '',
    '## Status',
    '',
    'DRY RUN - PR NOT CREATED',
    '',
    '## Problem',
    '',
    input.problem,
    '',
    '## Root Cause',
    '',
    input.rootCause,
    '',
    `## Risk\n\n${input.riskLevel}`,
    '',
    `## Branch\n\n\`${input.branchName}\``,
    '',
    '## Repair Plan',
    '',
    ...input.repairPlan.map((step) => `- ${step}`),
    '',
    '## Validation',
    '',
    ...input.validation.map((check) => `- ${check}`),
    '',
    `## Guardian Issue\n\n${input.issueNumber ? `#${input.issueNumber}` : 'Not assigned'}`,
    '',
    'Automatic merge is disabled. Human review is required.',
    '',
  ].join('\n');
}

export function canCreatePullRequest(config: { mode: string; prMode: string; autoMerge: boolean }): { allowed: boolean; reason: string } {
  if (config.autoMerge) return { allowed: false, reason: 'Automatic merge is permanently disabled for this phase.' };
  if (config.mode !== 'active' || config.prMode !== 'active') return { allowed: false, reason: 'Pull-request creation is disabled.' };
  if (process.env.GUARDIAN_ACTIVE_AUTOMATION !== 'true') return { allowed: false, reason: 'GUARDIAN_ACTIVE_AUTOMATION is not enabled.' };
  return { allowed: true, reason: 'Pull-request creation would require a separately authorized executor.' };
}
