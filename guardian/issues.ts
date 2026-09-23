export interface GuardianIssueInput {
  repository: string;
  token: string;
  title: string;
  fingerprint: string;
  severity: string;
  check: string;
  affectedUrl?: string;
  error: string;
  evidence: string[];
  labels: string[];
}

const apiBase = 'https://api.github.com';

function headers(token: string): Record<string, string> {
  return {
    Accept: 'application/vnd.github+json',
    Authorization: `Bearer ${token}`,
    'User-Agent': 'ai-portfolio-guardian',
    'X-GitHub-Api-Version': '2022-11-28',
  };
}

export function makeFingerprint(parts: string[]): string {
  return parts.map((part) => part.trim().toLowerCase().replace(/\s+/g, '-')).join(':');
}

export function issueBody(input: Omit<GuardianIssueInput, 'repository' | 'token' | 'labels'> & { firstDetected?: string; lastDetected?: string }): string {
  const detected = input.firstDetected ?? new Date().toISOString();
  const lastDetected = input.lastDetected ?? detected;
  return [
    '<!-- guardian-fingerprint:',
    input.fingerprint,
    '-->',
    '',
    '# Guardian detected a portfolio problem',
    '',
    '## Status',
    '',
    'Detected',
    '',
    `## Severity\n\n${input.severity}`,
    '',
    `## Check\n\n${input.check}`,
    '',
    `## Fingerprint\n\n\`${input.fingerprint}\``,
    '',
    `## Affected URL\n\n${input.affectedUrl ? `\`${input.affectedUrl}\`` : 'Not provided'}`,
    '',
    `## Error\n\n${input.error}`,
    '',
    `## First detected\n\n${detected}`,
    '',
    `## Last detected\n\n${lastDetected}`,
    '',
    '## Evidence',
    '',
    ...input.evidence.map((item) => `- ${item}`),
    '',
    '## AI Diagnosis',
    '',
    'Pending',
    '',
    '## AI Risk Classification',
    '',
    'Pending',
    '',
    '## Repair',
    '',
    'Pending',
    '',
    '## Validation',
    '',
    'Pending',
    '',
  ].join('\n');
}

async function githubRequest<T>(repository: string, token: string, endpoint: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}/repos/${repository}${endpoint}`, {
    ...init,
    headers: { ...headers(token), ...(init?.headers ?? {}) },
  });
  if (!response.ok) throw new Error(`GitHub API ${response.status}: ${await response.text()}`);
  return response.json() as Promise<T>;
}

interface GithubIssue {
  number: number;
  body?: string;
  html_url: string;
}

export function findIssueByFingerprint(issues: GithubIssue[], fingerprint: string): GithubIssue | undefined {
  return issues.find((issue) => issue.body?.includes(`guardian-fingerprint:\n${fingerprint}\n`));
}

export async function ensureLabels(repository: string, token: string, labels: string[]): Promise<void> {
  for (const name of labels) {
    const encoded = encodeURIComponent(name);
    const existing = await fetch(`${apiBase}/repos/${repository}/labels/${encoded}`, { headers: headers(token) });
    if (existing.status === 404) {
      await githubRequest(repository, token, '/labels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
    } else if (!existing.ok) {
      throw new Error(`Unable to inspect GitHub label ${name}: ${existing.status}`);
    }
  }
}

export async function upsertGuardianIssue(input: GuardianIssueInput): Promise<{ number: number; url: string; created: boolean }> {
  await ensureLabels(input.repository, input.token, input.labels);
  const issues = await githubRequest<GithubIssue[]>(input.repository, input.token, '/issues?state=open&labels=guardian&per_page=100');
  const existing = findIssueByFingerprint(issues, input.fingerprint);
  const body = issueBody(input);
  if (existing) {
    const updated = await githubRequest<GithubIssue>(input.repository, input.token, `/issues/${existing.number}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body, labels: input.labels }),
    });
    return { number: updated.number, url: updated.html_url, created: false };
  }
  const created = await githubRequest<GithubIssue>(input.repository, input.token, '/issues', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: input.title, body, labels: input.labels }),
  });
  return { number: created.number, url: created.html_url, created: true };
}
