import { loadAutomationPolicy } from '../ai/policy.js';

export interface DiffSummary {
  filesChanged: string[];
  linesChanged: number;
  binaryFiles?: string[];
}

export async function validateDiff(summary: DiffSummary): Promise<{ valid: boolean; reasons: string[] }> {
  const policy = await loadAutomationPolicy();
  const reasons: string[] = [];
  if (summary.filesChanged.length > policy.autoFix.maximumFilesChanged) reasons.push('Diff changes too many files.');
  if (summary.linesChanged > policy.autoFix.maximumLinesChanged) reasons.push('Diff changes too many lines.');
  if ((summary.binaryFiles ?? []).length > 0) reasons.push('Binary file changes are not allowed.');
  for (const file of summary.filesChanged) {
    if (policy.protectedPaths.some((protectedPath) => file === protectedPath || file.startsWith(protectedPath))) reasons.push(`Diff changes protected path: ${file}`);
  }
  return { valid: reasons.length === 0, reasons };
}
