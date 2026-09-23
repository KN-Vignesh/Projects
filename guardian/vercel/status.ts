export interface VercelStatus {
  status: 'NOT_ENABLED';
  reason: string;
}

export async function getVercelStatus(): Promise<VercelStatus> {
  return {
    status: 'NOT_ENABLED',
    reason: 'Vercel API verification is disabled until credentials and project identity are explicitly configured.',
  };
}
