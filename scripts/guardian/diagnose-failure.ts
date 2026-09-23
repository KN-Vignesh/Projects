import { readFile, writeFile } from 'node:fs/promises';
import { createAiClient } from '../../guardian/ai/client.js';
import { buildDiagnosisPrompt } from '../../guardian/ai/prompt.js';
import { parseDiagnosisJson } from '../../guardian/ai/validator.js';
import { evaluateAutoFixPolicy } from '../../guardian/ai/policy.js';

const evidencePath = process.env.GUARDIAN_FAILURE_FILE ?? 'guardian/failure.json';
const evidence = JSON.parse(await readFile(evidencePath, 'utf8'));
const client = createAiClient();
const rawDiagnosis = await client.complete(buildDiagnosisPrompt(evidence));
const diagnosis = parseDiagnosisJson(rawDiagnosis);
const policy = await evaluateAutoFixPolicy(diagnosis);
const result = { diagnosis, policy, diagnosedAt: new Date().toISOString() };
await writeFile('guardian/reports/diagnosis.json', `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
