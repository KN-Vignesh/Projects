export interface BranchConfig {
  mode: 'observe' | 'dry-run' | 'active';
  repairMode: 'disabled' | 'active';
  baseBranch: string;
}

export interface BranchPreview {
  status: 'simulated' | 'blocked' | 'ready';
  branchName: string;
  baseBranch: string;
  baseCommit: string | null;
  reason: string;
}

export function buildBranchName(fingerprint: string): string {
  const suffix = fingerprint.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 64);
  return `guardian/fix/${suffix || 'repair'}`;
}

export function planRepairBranch(fingerprint: string, config: BranchConfig, baseCommit: string | null): BranchPreview {
  const branchName = buildBranchName(fingerprint);
  if (config.mode === 'dry-run') return { status: 'simulated', branchName, baseBranch: config.baseBranch, baseCommit, reason: 'Dry-run mode; branch would be created but was not.' };
  if (config.mode !== 'active' || config.repairMode !== 'active') return { status: 'blocked', branchName, baseBranch: config.baseBranch, baseCommit, reason: 'Repair branch creation is disabled.' };
  if (config.baseBranch === 'main') return { status: 'blocked', branchName, baseBranch: config.baseBranch, baseCommit, reason: 'A repair cannot operate from main.' };
  if (process.env.GUARDIAN_ACTIVE_AUTOMATION !== 'true') return { status: 'blocked', branchName, baseBranch: config.baseBranch, baseCommit, reason: 'GUARDIAN_ACTIVE_AUTOMATION is not enabled.' };
  return { status: 'ready', branchName, baseBranch: config.baseBranch, baseCommit, reason: 'Branch creation would require a separately authorized executor.' };
}
