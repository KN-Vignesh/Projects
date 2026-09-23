import { mkdir, writeFile } from 'node:fs/promises';
import { buildDryRunArtifacts } from '../../guardian/dry-run.js';

const config = JSON.parse(await (await import('node:fs/promises')).readFile('guardian/config.json', 'utf8')) as { mode: string };
if (config.mode !== 'dry-run') throw new Error(`Dry-run command requires guardian mode=dry-run, received ${config.mode}.`);

const artifacts = await buildDryRunArtifacts();
await mkdir('guardian-evidence', { recursive: true });
await writeFile('guardian-evidence/failures.json', `${JSON.stringify([artifacts.failure], null, 2)}\n`);
await writeFile('guardian-evidence/manifest.json', `${JSON.stringify({
  timestamp: new Date().toISOString(),
  repository: process.env.GITHUB_REPOSITORY ?? 'KN-Vignesh/Projects',
  commit: process.env.GITHUB_SHA ?? null,
  branch: process.env.GITHUB_REF_NAME ?? 'local',
  environment: 'dry-run',
  status: 'failed',
  checks: [{ name: artifacts.failure.check, status: 'failed', artifact: 'failures.json' }],
}, null, 2)}\n`);
await writeFile('guardian-issue-preview.md', artifacts.issuePreview);
await writeFile('guardian-ai-diagnosis.json', `${JSON.stringify(artifacts.diagnosis, null, 2)}\n`);
await writeFile('guardian-ai-diagnosis.md', `# Guardian AI Diagnosis\n\nStatus: DRY RUN - NO AI SOURCE MODIFICATION\n\n${artifacts.diagnosis.rootCause}\n`);
await writeFile('guardian-repair-plan.json', `${JSON.stringify({ status: 'REPAIR NOT APPLIED - DRY RUN', policy: artifacts.policy, validation: artifacts.repairValidation, repairPlan: artifacts.repairPlan }, null, 2)}\n`);
await writeFile('guardian-repair-plan.md', `# Guardian Repair Plan\n\nREPAIR NOT APPLIED - DRY RUN\n\n${artifacts.diagnosis.proposedFix}\n`);
await writeFile('guardian-branch-preview.json', `${JSON.stringify(artifacts.branchPreview, null, 2)}\n`);
await writeFile('guardian-pr-preview.md', artifacts.prPreview);
console.log(JSON.stringify({
  mode: config.mode,
  fingerprint: artifacts.fingerprint,
  issue: 'WOULD CREATE/UPDATE ISSUE',
  diagnosis: 'WOULD RUN AI DIAGNOSIS',
  branch: 'WOULD CREATE BRANCH',
  source: 'WOULD MODIFY FILE - BLOCKED',
  pullRequest: 'WOULD CREATE PR',
  policy: artifacts.policy,
}, null, 2));
