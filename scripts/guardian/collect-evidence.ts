import { cp, mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

const reportDirectory = path.join(process.cwd(), 'guardian', 'reports');
const evidenceDirectory = path.join(process.cwd(), 'guardian-evidence');
const reportFiles = [
  'links.json',
  'code-repository.json',
  'npm-audit.json',
  'guardian-report.json',
  'diagnosis.json',
];

await mkdir(evidenceDirectory, { recursive: true });
const copied: string[] = [];
for (const file of reportFiles) {
  try {
    await cp(path.join(reportDirectory, file), path.join(evidenceDirectory, file));
    copied.push(file);
  } catch {
    // Reports are optional because individual checks can fail before producing output.
  }
}

let failures: unknown[] = [];
try {
  const links = JSON.parse(await readFile(path.join(reportDirectory, 'links.json'), 'utf8')) as { checks?: Array<{ healthy: boolean; target: string; message: string }> };
  failures = (links.checks ?? []).filter((check) => !check.healthy);
} catch {
  // The manifest records missing evidence instead of failing collection itself.
}

const manifest = {
  timestamp: new Date().toISOString(),
  repository: process.env.GITHUB_REPOSITORY ?? 'KN-Vignesh/Projects',
  commit: process.env.GITHUB_SHA ?? null,
  branch: process.env.GITHUB_REF_NAME ?? 'local',
  environment: process.env.GUARDIAN_ENVIRONMENT ?? 'ci',
  status: failures.length > 0 ? 'failed' : 'collected',
  artifacts: copied,
  failures: failures.length,
};

await writeFile(path.join(evidenceDirectory, 'summary.json'), `${JSON.stringify({ manifest, failures }, null, 2)}\n`);
await writeFile(path.join(evidenceDirectory, 'failures.json'), `${JSON.stringify(failures, null, 2)}\n`);
await writeFile(path.join(evidenceDirectory, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(JSON.stringify(manifest, null, 2));
