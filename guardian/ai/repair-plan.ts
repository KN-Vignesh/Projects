import { access } from 'node:fs/promises';
import path from 'node:path';
import { loadAutomationPolicy } from './policy.js';

export interface RepairPlanItem {
  file: string;
  action: 'update' | 'create';
  reason: string;
  change: string;
}

export async function validateRepairPlan(plan: RepairPlanItem[]): Promise<{ valid: boolean; reasons: string[] }> {
  const policy = await loadAutomationPolicy();
  const reasons: string[] = [];
  for (const item of plan) {
    if (!item.file || path.isAbsolute(item.file) || item.file.includes('..')) reasons.push(`Invalid file path: ${item.file}`);
    if (!['update', 'create'].includes(item.action)) reasons.push(`Unsupported action: ${item.action}`);
    if (policy.protectedPaths.some((protectedPath) => item.file === protectedPath || item.file.startsWith(protectedPath))) {
      reasons.push(`Protected path: ${item.file}`);
    }
    if (item.action === 'update') {
      try {
        await access(path.join(process.cwd(), item.file));
      } catch {
        reasons.push(`Update target does not exist: ${item.file}`);
      }
    }
  }
  return { valid: reasons.length === 0, reasons };
}