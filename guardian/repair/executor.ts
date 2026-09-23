import { readFile, writeFile } from 'node:fs/promises';
import { validateStructuredRepairOperations, type StructuredRepairPlan } from '../ai/repair-plan.js';
import { validateDiff } from './diff.js';

export interface RepairExecutionResult {
  status: 'blocked' | 'dry-run' | 'applied' | 'failed';
  reason: string;
  filesChanged: string[];
  operationsApplied: number;
}

interface RepairConfig {
  mode: 'observe' | 'dry-run' | 'active';
  repairMode: 'disabled' | 'active';
  automation: { sourceModification: boolean };
}

export async function executeRepairPlan(plan: StructuredRepairPlan, config: RepairConfig, currentBranch: string): Promise<RepairExecutionResult> {
  const policy = await validateStructuredRepairOperations(plan);
  if (!policy.valid) return { status: 'blocked', reason: policy.reasons.join(' '), filesChanged: [], operationsApplied: 0 };
  if (config.mode !== 'active' || config.repairMode !== 'active' || !config.automation.sourceModification) {
    return { status: 'dry-run', reason: 'Repair is disabled by configuration.', filesChanged: [], operationsApplied: 0 };
  }
  if (process.env.GUARDIAN_ACTIVE_AUTOMATION !== 'true') return { status: 'blocked', reason: 'GUARDIAN_ACTIVE_AUTOMATION is not enabled.', filesChanged: [], operationsApplied: 0 };
  if (!currentBranch || currentBranch === 'main') return { status: 'blocked', reason: 'Repairs cannot run on main.', filesChanged: [], operationsApplied: 0 };

  const originals = new Map<string, string>();
  try {
    for (const operation of plan.operations) {
      const original = originals.get(operation.file) ?? await readFile(operation.file, 'utf8');
      originals.set(operation.file, original);
      const occurrences = original.split(operation.oldValue).length - 1;
      if (occurrences !== 1) throw new Error(`${operation.file} expected exactly one old-value match, found ${occurrences}.`);
      const updated = original.replace(operation.oldValue, operation.newValue);
      await writeFile(operation.file, updated);
    }
    const diff = await validateDiff({
      filesChanged: [...originals.keys()],
      linesChanged: plan.operations.reduce((total, operation) => total + operation.oldValue.split(/\r?\n/).length + operation.newValue.split(/\r?\n/).length, 0),
    });
    if (!diff.valid) throw new Error(diff.reasons.join(' '));
    return { status: 'applied', reason: 'Controlled repair operations applied.', filesChanged: [...originals.keys()], operationsApplied: plan.operations.length };
  } catch (error) {
    for (const [file, original] of originals) await writeFile(file, original);
    return { status: 'failed', reason: error instanceof Error ? error.message : 'Repair failed.', filesChanged: [], operationsApplied: 0 };
  }
}