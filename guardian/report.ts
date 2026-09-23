import { readFile } from 'node:fs/promises';
import path from 'node:path';

export type CheckStatus = 'passed' | 'failed' | 'warning' | 'not-run';

export interface GuardianReport {
  timestamp: string;
  repository: string;
  commit: string | null;
  environment: string;
  status: 'healthy' | 'degraded' | 'failed';
  checks: Record<string, CheckStatus>;
  issues: string[];
  ai: {
    diagnosed: number;
    autoFixed: number;
    pullRequestsCreated: number;
  };
  automation: {
    mode: 'observe' | 'dry-run' | 'active';
    issueCreation: 'enabled' | 'simulated' | 'disabled';
    aiDiagnosis: 'enabled' | 'simulated' | 'disabled';
    sourceModification: 'enabled' | 'blocked' | 'disabled';
    repair: 'enabled' | 'simulated' | 'disabled';
    branchCreation: 'enabled' | 'simulated' | 'disabled';
    pullRequestCreation: 'enabled' | 'simulated' | 'disabled';
    pullRequest: 'enabled' | 'simulated' | 'disabled';
    autoMerge: 'enabled' | 'disabled';
    vercelApi: 'enabled' | 'disabled';
    rollback: 'enabled' | 'disabled';
  };
}

interface StoredCheck {
  healthy?: boolean;
}

async function readCheckStatus(filePath: string): Promise<CheckStatus> {
  try {
    const check = JSON.parse(await readFile(filePath, 'utf8')) as StoredCheck;
    return check.healthy === true ? 'passed' : 'failed';
  } catch {
    return 'not-run';
  }
}

async function statusFromEnvironmentOrReport(name: string, filePath: string): Promise<CheckStatus> {
  return (process.env[name] as CheckStatus | undefined) ?? readCheckStatus(filePath);
}

async function readAutomationConfig() {
  try {
    return JSON.parse(await readFile(path.join(process.cwd(), 'guardian', 'config.json'), 'utf8')) as {
      mode: 'observe' | 'dry-run' | 'active';
      issueMode?: 'dry-run' | 'active';
      aiDiagnosisMode?: 'dry-run' | 'active';
      repairMode?: 'disabled' | 'active';
      prMode?: 'disabled' | 'active';
      automation: Record<string, boolean>;
    };
  } catch {
    return {
      mode: 'dry-run' as const,
      issueMode: 'dry-run' as const,
      aiDiagnosisMode: 'dry-run' as const,
      automation: {},
    };
  }
}

export async function buildGuardianReport(environment = process.env.GUARDIAN_ENVIRONMENT ?? 'ci') {
  const reportsDirectory = path.join(process.cwd(), 'guardian', 'reports');
  const checks = {
    typescript: (process.env.GUARDIAN_TYPESCRIPT_STATUS as CheckStatus) ?? 'not-run',
    build: (process.env.GUARDIAN_BUILD_STATUS as CheckStatus) ?? 'not-run',
    playwright: (process.env.GUARDIAN_PLAYWRIGHT_STATUS as CheckStatus) ?? 'not-run',
    accessibility: (process.env.GUARDIAN_ACCESSIBILITY_STATUS as CheckStatus) ?? 'not-run',
    lighthouse: (process.env.GUARDIAN_LIGHTHOUSE_STATUS as CheckStatus) ?? 'not-run',
    links: await statusFromEnvironmentOrReport('GUARDIAN_LINKS_STATUS', path.join(reportsDirectory, 'links.json')),
    projectReferences: await statusFromEnvironmentOrReport('GUARDIAN_PROJECT_REFERENCES_STATUS', path.join(reportsDirectory, 'code-repository.json')),
    dependencies: (process.env.GUARDIAN_DEPENDENCIES_STATUS as CheckStatus) ?? 'not-run',
    productionSmoke: (process.env.GUARDIAN_PRODUCTION_STATUS as CheckStatus) ?? 'not-run',
  };
  const failed = Object.values(checks).filter((status) => status === 'failed');
  const warnings = Object.values(checks).filter((status) => status === 'warning');
  const notRun = Object.values(checks).filter((status) => status === 'not-run');
  const repository = process.env.GITHUB_REPOSITORY ?? 'KN-Vignesh/Projects';
  const automationConfig = await readAutomationConfig();
  const mode = automationConfig.mode;
  const state = (enabled: boolean) => mode === 'dry-run' ? 'simulated' : enabled && mode === 'active' ? 'enabled' : 'disabled';

  return {
    timestamp: new Date().toISOString(),
    repository,
    commit: process.env.GITHUB_SHA ?? null,
    environment,
    status: failed.length > 0 ? 'failed' : warnings.length > 0 || notRun.length > 0 ? 'degraded' : 'healthy',
    checks,
    issues: [],
    ai: { diagnosed: 0, autoFixed: 0, pullRequestsCreated: 0 },
    automation: {
      mode,
      issueCreation: environment === 'dry-run'
        ? 'simulated'
        : automationConfig.issueMode === 'active'
          ? 'enabled'
          : state(automationConfig.automation.issueCreation) as GuardianReport['automation']['issueCreation'],
      aiDiagnosis: environment === 'dry-run'
        ? 'simulated'
        : automationConfig.aiDiagnosisMode === 'active'
          ? 'enabled'
          : state(automationConfig.automation.aiDiagnosis) as GuardianReport['automation']['aiDiagnosis'],
      sourceModification: automationConfig.automation.sourceModification && mode === 'active' ? 'enabled' : 'blocked',
      repair: environment === 'dry-run' ? 'simulated' : automationConfig.repairMode === 'active' && mode === 'active' ? 'enabled' : 'disabled',
      branchCreation: state(automationConfig.automation.branchCreation) as GuardianReport['automation']['branchCreation'],
      pullRequestCreation: state(automationConfig.automation.pullRequestCreation) as GuardianReport['automation']['pullRequestCreation'],
      pullRequest: environment === 'dry-run' ? 'simulated' : automationConfig.prMode === 'active' && mode === 'active' ? 'enabled' : 'disabled',
      autoMerge: automationConfig.automation.autoMerge && mode === 'active' ? 'enabled' : 'disabled',
      vercelApi: automationConfig.automation.vercelApi && mode === 'active' ? 'enabled' : 'disabled',
      rollback: automationConfig.automation.rollback && mode === 'active' ? 'enabled' : 'disabled',
    },
  } satisfies GuardianReport;
}
