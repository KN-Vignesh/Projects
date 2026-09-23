import { riskLevels, type Diagnosis } from './types.js';

const requiredKeys = [
  'problem',
  'rootCause',
  'confidence',
  'affectedFiles',
  'affectedRoutes',
  'evidence',
  'proposedFix',
  'repairPlan',
  'riskLevel',
  'autoFixAllowed',
  'requiresHumanReview',
] as const;

export function validateDiagnosis(value: unknown): Diagnosis {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Diagnosis must be an object.');
  const diagnosis = value as Record<string, unknown>;
  for (const key of requiredKeys) if (!(key in diagnosis)) throw new Error(`Diagnosis is missing ${key}.`);
  if (Object.keys(diagnosis).some((key) => !requiredKeys.includes(key as (typeof requiredKeys)[number]))) {
    throw new Error('Diagnosis contains unexpected fields.');
  }
  for (const key of ['problem', 'rootCause', 'proposedFix'] as const) {
    if (typeof diagnosis[key] !== 'string' || diagnosis[key].trim() === '') throw new Error(`${key} must be a non-empty string.`);
  }
  for (const key of ['affectedFiles', 'affectedRoutes', 'evidence', 'repairPlan'] as const) {
    if (!Array.isArray(diagnosis[key]) || diagnosis[key].some((item) => typeof item !== 'string')) throw new Error(`${key} must be a string array.`);
  }
  if (typeof diagnosis.confidence !== 'number' || diagnosis.confidence < 0 || diagnosis.confidence > 1) throw new Error('confidence must be between 0 and 1.');
  if (!riskLevels.includes(diagnosis.riskLevel as Diagnosis['riskLevel'])) throw new Error('riskLevel is invalid.');
  if (typeof diagnosis.autoFixAllowed !== 'boolean' || typeof diagnosis.requiresHumanReview !== 'boolean') throw new Error('Automation flags must be booleans.');
  if ((diagnosis.riskLevel === 'high' || diagnosis.riskLevel === 'critical') && diagnosis.autoFixAllowed) throw new Error('High and critical diagnoses cannot be auto-fixed.');
  if (diagnosis.autoFixAllowed && !diagnosis.requiresHumanReview) throw new Error('Automatic fixes still require human review.');
  return diagnosis as Diagnosis;
}

export function parseDiagnosisJson(text: string): Diagnosis {
  try {
    return validateDiagnosis(JSON.parse(text));
  } catch (error) {
    throw new Error(`Invalid AI diagnosis: ${error instanceof Error ? error.message : 'unknown error'}`);
  }
}
