import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { commentOnIssue } from '../../guardian/issues.js';
import { createAiClient } from '../../guardian/ai/client.js';
import { buildDiagnosisPrompt } from '../../guardian/ai/prompt.js';
import { evaluateAutoFixPolicy } from '../../guardian/ai/policy.js';
import { parseDiagnosisJson } from '../../guardian/ai/validator.js';

interface IssueResult {
  fingerprint: string;
  issueNumber: number;
  issueUrl: string;
  failure: Record<string, unknown>;
}

interface IssueHandoff {
  issues: IssueResult[];
}

const config = JSON.parse(await readFile('guardian/config.json', 'utf8')) as { aiDiagnosisMode?: string };
const token = process.env.GITHUB_TOKEN;
const repository = process.env.GITHUB_REPOSITORY;
let handoff: IssueHandoff = { issues: [] };
try {
  handoff = JSON.parse(await readFile('guardian/reports/issue-results.json', 'utf8')) as IssueHandoff;
} catch {
  console.log('No issue handoff evidence found; diagnosis has no issues to process.');
}
const results: Array<Record<string, unknown>> = [];

if (config.aiDiagnosisMode !== 'active') {
  console.log('AI diagnosis is not active; no provider call or Issue comment was attempted.');
  process.exit(0);
}
if (!token || !repository) throw new Error('GITHUB_TOKEN and GITHUB_REPOSITORY are required for diagnosis comments.');

let client: ReturnType<typeof createAiClient> | null = null;
try {
  client = createAiClient();
} catch (error) {
  const message = error instanceof Error ? error.message : 'AI configuration is unavailable.';
  for (const issue of handoff.issues) {
    await commentOnIssue(repository, token, issue.issueNumber, `## AI Portfolio Guardian\n\nAI diagnosis unavailable.\n\n${message}\n\nNo repair was attempted.`);
    results.push({ fingerprint: issue.fingerprint, issueNumber: issue.issueNumber, status: 'unavailable' });
  }
}

if (client) {
  for (const issue of handoff.issues) {
    try {
      const raw = await client.complete(buildDiagnosisPrompt({ fingerprint: issue.fingerprint, issueUrl: issue.issueUrl, failure: issue.failure }));
      const diagnosis = parseDiagnosisJson(raw);
      const policy = await evaluateAutoFixPolicy(diagnosis);
      const output = { fingerprint: issue.fingerprint, issueNumber: issue.issueNumber, status: 'validated', diagnosis, policy };
      await commentOnIssue(repository, token, issue.issueNumber, [
        '## AI Portfolio Guardian Diagnosis',
        '',
        'Diagnosis validated. No source modification, branch, PR, merge, or deployment action was performed.',
        '',
        '```json',
        JSON.stringify(output, null, 2),
        '```',
      ].join('\n'));
      results.push(output);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'AI diagnosis validation failed.';
      await commentOnIssue(repository, token, issue.issueNumber, `## AI Portfolio Guardian\n\nAI diagnosis invalid or unavailable: ${message}\n\nNo repair was attempted.`);
      results.push({ fingerprint: issue.fingerprint, issueNumber: issue.issueNumber, status: 'invalid', error: message });
    }
  }
}

const report = { diagnosedAt: new Date().toISOString(), issues: results };
await mkdir('guardian/reports', { recursive: true });
await writeFile('guardian/reports/diagnosis-results.json', `${JSON.stringify(report, null, 2)}\n`);
await writeFile('guardian-ai-diagnosis.json', `${JSON.stringify(report, null, 2)}\n`);
await writeFile('guardian-ai-diagnosis.md', [
  '# Guardian AI Diagnosis',
  '',
  'No source modification, branch creation, PR, merge, deployment, or rollback is enabled in Phase C.',
  '',
  ...results.map((result) => `- Issue #${result.issueNumber}: ${result.status}`),
  '',
].join('\n'));