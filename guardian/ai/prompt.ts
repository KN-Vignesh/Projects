export function buildDiagnosisPrompt(evidence: unknown): string {
  return [
    'You are an AI software reliability engineer.',
    'Use only the supplied Guardian evidence. Do not guess or invent files.',
    'Identify the smallest likely root cause and distinguish symptoms from evidence-backed causes.',
    'Do not propose unrelated refactoring, dependency upgrades, workflow changes, secret changes, or deployment changes.',
    'Any repair must remain on a branch and require a human-reviewed pull request.',
    'Return only JSON matching the Guardian diagnosis schema.',
    '',
    JSON.stringify(evidence, null, 2),
  ].join('\n');
}
