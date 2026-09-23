import { access } from 'node:fs/promises';
import path from 'node:path';
import { loadAutomationPolicy } from './policy.js';

export const repairOperationTypes = [
  'update_internal_link',
  'update_project_reference',
  'update_route_reference',
  'add_accessibility_attribute',
  'update_documentation_reference',
] as const;
export type RepairOperationType = (typeof repairOperationTypes)[number];

export interface RepairOperation {
  type: RepairOperationType;
  file: string;
  oldValue: string;
  newValue: string;
}

export interface StructuredRepairPlan {
  repairId: string;
  fingerprint: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  operations: RepairOperation[];
  reason: string;
  expectedValidation: string[];
}

export interface RepairPlanItem {
  file: string;
  action: 'update' | 'create';
  reason: string;
  change: string;
}

export function validateStructuredRepairPlan(value: unknown, expectedFingerprint?: string): StructuredRepairPlan {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Repair plan must be an object.');
  const plan = value as Record<string, unknown>;
  for (const key of ['repairId', 'fingerprint', 'riskLevel', 'confidence', 'operations', 'reason', 'expectedValidation']) {
    if (!(key in plan)) throw new Error(`Repair plan is missing ${key}.`);
  }
  if (typeof plan.repairId !== 'string' || !plan.repairId.trim()) throw new Error('repairId must be non-empty.');
  if (typeof plan.fingerprint !== 'string' || !plan.fingerprint.trim()) throw new Error('fingerprint must be non-empty.');
  if (expectedFingerprint && plan.fingerprint !== expectedFingerprint) throw new Error('Repair fingerprint does not match the failure fingerprint.');
  if (!['low', 'medium', 'high', 'critical'].includes(String(plan.riskLevel))) throw new Error('Repair risk level is invalid.');
  if (typeof plan.confidence !== 'number' || plan.confidence < 0 || plan.confidence > 1) throw new Error('Repair confidence must be between 0 and 1.');
  if (!Array.isArray(plan.operations) || plan.operations.length === 0) throw new Error('Repair plan must contain operations.');
  if (typeof plan.reason !== 'string' || !plan.reason.trim()) throw new Error('Repair reason must be non-empty.');
  if (!Array.isArray(plan.expectedValidation) || plan.expectedValidation.some((item) => typeof item !== 'string')) throw new Error('expectedValidation must be a string array.');
  for (const operation of plan.operations) {
    if (!operation || typeof operation !== 'object') throw new Error('Repair operation must be an object.');
    const candidate = operation as Record<string, unknown>;
    if (!repairOperationTypes.includes(candidate.type as RepairOperationType)) throw new Error(`Unsupported repair operation: ${String(candidate.type)}.`);
    for (const key of ['file', 'oldValue', 'newValue']) {
      if (typeof candidate[key] !== 'string' || !candidate[key]) throw new Error(`Repair operation ${key} must be non-empty.`);
    }
    if (candidate.oldValue === candidate.newValue) throw new Error('Repair operation must change its value.');
  }
  return plan as unknown as StructuredRepairPlan;
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

export async function validateStructuredRepairOperations(plan: StructuredRepairPlan): Promise<{ valid: boolean; reasons: string[] }> {
  const policy = await loadAutomationPolicy();
  const reasons: string[] = [];
  if (plan.riskLevel !== 'low') reasons.push(`Risk level ${plan.riskLevel} is not eligible for automatic repair.`);
  if (plan.confidence < policy.autoFix.minimumConfidence) reasons.push(`Confidence ${plan.confidence} is below ${policy.autoFix.minimumConfidence}.`);
  if (plan.operations.length > policy.autoFix.maximumFilesChanged) reasons.push('Repair exceeds the maximum operation count.');
  for (const operation of plan.operations) {
    if (path.isAbsolute(operation.file) || operation.file.includes('..')) reasons.push(`Invalid repair path: ${operation.file}`);
    if (policy.protectedPaths.some((protectedPath) => operation.file === protectedPath || operation.file.startsWith(protectedPath))) reasons.push(`Protected repair path: ${operation.file}`);
    try {
      await access(path.join(process.cwd(), operation.file));
    } catch {
      reasons.push(`Repair file does not exist: ${operation.file}`);
    }
  }
  return { valid: reasons.length === 0, reasons };
}