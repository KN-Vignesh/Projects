import { readFile } from 'node:fs/promises';
import path from 'node:path';
import type { Diagnosis } from './types.js';

interface AutomationPolicy {
  autoFix: {
    enabled: boolean;
    allowedRiskLevels: string[];
    requiresValidation: boolean;
    requiresPullRequest: boolean;
    autoMerge: boolean;
    minimumConfidence: number;
    maximumFilesChanged: number;
    maximumLinesChanged: number;
  };
  protectedPaths: string[];
}

export async function loadAutomationPolicy(): Promise<AutomationPolicy> {
  return JSON.parse(await readFile(path.join(process.cwd(), 'guardian', 'policies', 'automation-policy.json'), 'utf8')) as AutomationPolicy;
}

export async function evaluateAutoFixPolicy(diagnosis: Diagnosis): Promise<{ allowed: boolean; reasons: string[] }> {
  const policy = await loadAutomationPolicy();
  const reasons: string[] = [];
  if (!policy.autoFix.enabled) reasons.push('Automatic repair is disabled.');
  if (!policy.autoFix.allowedRiskLevels.includes(diagnosis.riskLevel)) reasons.push(`Risk level ${diagnosis.riskLevel} is not allowed.`);
  if (!diagnosis.autoFixAllowed) reasons.push('Diagnosis does not allow automatic repair.');
  if (!diagnosis.requiresHumanReview) reasons.push('Human review is required for every repair.');
  for (const file of diagnosis.affectedFiles) {
    if (policy.protectedPaths.some((protectedPath) => file === protectedPath || file.startsWith(protectedPath))) {
      reasons.push(`Protected path: ${file}`);
    }
  }
  return { allowed: reasons.length === 0, reasons };
}
