import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';

interface ProjectLink {
  name: string;
  path: string;
  kind: 'file' | 'directory';
  required: boolean;
  portfolioRoute: string;
}

interface ProjectManifest {
  repository: string;
  projects: ProjectLink[];
}

interface RepositoryCheck {
  name: string;
  path: string;
  kind: ProjectLink['kind'];
  required: boolean;
  status: number | null;
  healthy: boolean;
  message: string;
}

const root = process.cwd();
const manifestPath = path.join(root, 'guardian', 'project-links.json');
const reportDirectory = path.join(root, 'guardian', 'reports');
const manifest = JSON.parse(await readFile(manifestPath, 'utf8')) as ProjectManifest;
const token = process.env.GITHUB_TOKEN;
const headers: Record<string, string> = {
  Accept: 'application/vnd.github+json',
  'User-Agent': 'ai-portfolio-guardian',
  'X-GitHub-Api-Version': '2022-11-28',
};
if (token) headers.Authorization = `Bearer ${token}`;

async function checkProject(project: ProjectLink): Promise<RepositoryCheck> {
  const encodedPath = project.path.split('/').map(encodeURIComponent).join('/');
  const apiUrl = `https://api.github.com/repos/${manifest.repository}/contents/${encodedPath}`;

  try {
    const response = await fetch(apiUrl, { headers });
    const healthy = response.ok;
    return {
      name: project.name,
      path: project.path,
      kind: project.kind,
      required: project.required,
      status: response.status,
      healthy,
      message: healthy ? 'Repository path exists.' : `GitHub API returned ${response.status}.`,
    };
  } catch (error) {
    return {
      name: project.name,
      path: project.path,
      kind: project.kind,
      required: project.required,
      status: null,
      healthy: false,
      message: error instanceof Error ? error.message : 'Unknown request failure.',
    };
  }
}

const checks = await Promise.all(manifest.projects.map(checkProject));
const failedChecks = checks.filter((check) => check.required && !check.healthy);
const report = {
  check: 'code-repository-paths',
  repository: manifest.repository,
  checkedAt: new Date().toISOString(),
  healthy: failedChecks.length === 0,
  checks,
};

await mkdir(reportDirectory, { recursive: true });
await writeFile(path.join(reportDirectory, 'code-repository.json'), `${JSON.stringify(report, null, 2)}\n`);

const markdown = [
  '# Code Repository Check',
  '',
  `Repository: ${manifest.repository}`,
  `Checked: ${report.checkedAt}`,
  `Status: ${report.healthy ? 'HEALTHY' : 'FAILED'}`,
  '',
  '| Project | Path | Status | Message |',
  '| --- | --- | --- | --- |',
  ...checks.map((check) =>
    `| ${check.name} | \`${check.path}\` | ${check.healthy ? 'PASS' : 'FAIL'} | ${check.message} |`,
  ),
  '',
].join('\n');
await writeFile(path.join(reportDirectory, 'code-repository.md'), markdown);

for (const check of checks) {
  console.log(`${check.healthy ? 'PASS' : 'FAIL'} ${check.name}: ${check.path} (${check.message})`);
}
if (failedChecks.length > 0) process.exitCode = 1;
