export const riskLevels = ['low', 'medium', 'high', 'critical'] as const;
export type RiskLevel = (typeof riskLevels)[number];

export interface Diagnosis {
  problem: string;
  rootCause: string;
  confidence: number;
  affectedFiles: string[];
  affectedRoutes: string[];
  evidence: string[];
  proposedFix: string;
  repairPlan: string[];
  riskLevel: RiskLevel;
  autoFixAllowed: boolean;
  requiresHumanReview: boolean;
}
