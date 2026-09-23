import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { buildGuardianReport } from '../../guardian/report.js';

const environment = process.argv.find((argument) => argument.startsWith('--environment='))?.split('=')[1] ?? 'ci';
const report = await buildGuardianReport(environment);
const markdown = [
  '# AI Portfolio Guardian',
  '',
  `Status: **${report.status.toUpperCase()}**`,
  `Environment: ${report.environment}`,
  `Repository: ${report.repository}`,
  `Commit: ${report.commit ?? 'local'}`,
  `Timestamp: ${report.timestamp}`,
  '',
  '## Validation',
  '',
  '| Check | Status |',
  '| --- | --- |',
  ...Object.entries(report.checks).map(([check, status]) => `| ${check} | ${status.toUpperCase()} |`),
  '',
  '## Automation',
  '',
  ...Object.entries(report.automation).map(([name, status]) => `- ${name}: **${String(status).toUpperCase()}**`),
  '',
  '## AI',
  '',
  `Diagnosed: ${report.ai.diagnosed}`,
  `Auto-fixed: ${report.ai.autoFixed}`,
  `Pull requests created: ${report.ai.pullRequestsCreated}`,
  '',
].join('\n');

await mkdir(path.join(process.cwd(), 'guardian', 'reports'), { recursive: true });
await writeFile('guardian-report.json', `${JSON.stringify(report, null, 2)}\n`);
await writeFile('guardian-report.md', markdown);
await writeFile('guardian/reports/guardian-report.json', `${JSON.stringify(report, null, 2)}\n`);
await writeFile('guardian/reports/guardian-report.md', markdown);
console.log(markdown);
if (report.status === 'failed') process.exitCode = 1;
