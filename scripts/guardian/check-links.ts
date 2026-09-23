import { mkdir, readFile, readdir, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';

interface LinkCheck {
  source: string;
  target: string;
  status: number | null;
  healthy: boolean;
  severity: 'error' | 'warning';
  message: string;
}

const root = process.cwd();
const reportDirectory = path.join(root, 'guardian', 'reports');
const ignoredDirectories = new Set(['.git', 'node_modules', 'dist', 'coverage', 'reports']);
const sourceExtensions = new Set(['.md', '.html', '.tsx', '.ts', '.js', '.css']);

async function collectFiles(directory: string): Promise<string[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  const files: string[] = [];
  for (const entry of entries) {
    if (entry.isDirectory() && ignoredDirectories.has(entry.name)) continue;
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await collectFiles(entryPath)));
    else if (sourceExtensions.has(path.extname(entry.name))) files.push(entryPath);
  }
  return files;
}

function extractLinks(source: string): string[] {
  const links = new Set<string>();
  const markdownPattern = /!?\[[^\]]*\]\((https?:\/\/[^)\s]+|(?:\.\.\/|\.\/|\/)[^)\s]+)\)/g;
  const anchorPattern = /<a\b[^>]*href=["'](https?:\/\/[^"']+|(?:\.\.\/|\.\/|\/)[^"']+)["']/gi;
  for (const pattern of [markdownPattern, anchorPattern]) {
    for (const match of source.matchAll(pattern)) links.add(match[1].replace(/[),.;]+$/, ''));
  }
  return [...links];
}

async function checkLocalLink(sourceFile: string, target: string): Promise<LinkCheck> {
  const cleanTarget = target.split('#')[0].split('?')[0];
  if (!cleanTarget || cleanTarget === '/') {
    return {
      source: path.relative(root, sourceFile),
      target,
      status: 200,
      healthy: true,
      severity: 'error',
      message: 'Root route.',
    };
  }
  const targetPath = cleanTarget.startsWith('/')
    ? path.join(root, cleanTarget.slice(1))
    : path.resolve(path.dirname(sourceFile), cleanTarget);
  try {
    const targetStat = await stat(targetPath);
    return {
      source: path.relative(root, sourceFile),
      target,
      status: 200,
      healthy: targetStat.isFile() || targetStat.isDirectory(),
      severity: 'error',
      message: 'Local target exists.',
    };
  } catch {
    const productionUrl = process.env.PORTFOLIO_URL;
    if (cleanTarget.startsWith('/') && productionUrl) {
      return checkExternalLink(sourceFile, new URL(cleanTarget, productionUrl).toString());
    }
    return {
      source: path.relative(root, sourceFile),
      target,
      status: 404,
      healthy: cleanTarget.startsWith('/'),
      severity: cleanTarget.startsWith('/') ? 'warning' : 'error',
      message: cleanTarget.startsWith('/')
        ? 'Runtime route was not checked locally; set PORTFOLIO_URL to verify it.'
        : 'Local target does not exist.',
    };
  }
}

async function checkExternalLink(sourceFile: string, target: string): Promise<LinkCheck> {
  try {
    const response = await fetch(target, { method: 'GET', redirect: 'follow' });
    const isAntiBotResponse = response.status === 999;
    return {
      source: path.relative(root, sourceFile),
      target,
      status: response.status,
      healthy: response.ok || isAntiBotResponse,
      severity: isAntiBotResponse ? 'warning' : 'error',
      message: response.ok
        ? 'External target responded successfully.'
        : isAntiBotResponse
          ? 'HTTP 999; target may be blocking automated requests.'
          : `HTTP ${response.status}.`,
    };
  } catch (error) {
    return {
      source: path.relative(root, sourceFile),
      target,
      status: null,
      healthy: false,
      severity: 'error',
      message: error instanceof Error ? error.message : 'External request failed.',
    };
  }
}

const files = await collectFiles(root);
const checks: LinkCheck[] = [];
for (const file of files) {
  const source = await readFile(file, 'utf8');
  for (const target of extractLinks(source)) {
    if (target.startsWith('https://') || target.startsWith('http://')) checks.push(await checkExternalLink(file, target));
    else if (!target.startsWith('#')) checks.push(await checkLocalLink(file, target));
  }
}

const uniqueChecks = [...new Map(checks.map((check) => [`${check.source}:${check.target}`, check])).values()];
const failedChecks = uniqueChecks.filter((check) => !check.healthy && check.severity === 'error');
const report = {
  check: 'portfolio-links',
  checkedAt: new Date().toISOString(),
  healthy: failedChecks.length === 0,
  checkedLinks: uniqueChecks.length,
  checks: uniqueChecks,
};

await mkdir(reportDirectory, { recursive: true });
await writeFile(path.join(reportDirectory, 'links.json'), `${JSON.stringify(report, null, 2)}\n`);
await writeFile(
  path.join(reportDirectory, 'links.md'),
  [
    '# Portfolio Link Check',
    '',
    `Checked: ${report.checkedAt}`,
    `Links checked: ${report.checkedLinks}`,
    `Status: ${report.healthy ? 'HEALTHY' : 'FAILED'}`,
    '',
    '| Source | Target | Status | Message |',
    '| --- | --- | --- | --- |',
    ...uniqueChecks.map((check) =>
      `| ${check.source} | ${check.target} | ${check.healthy ? 'PASS' : check.severity === 'warning' ? 'WARN' : 'FAIL'} | ${check.message} |`,
    ),
    '',
  ].join('\n'),
);

for (const check of uniqueChecks) {
  const status = check.healthy ? check.severity === 'warning' ? 'WARN' : 'PASS' : 'FAIL';
  console.log(`${status} ${check.target}: ${check.message}`);
}
if (failedChecks.length > 0) process.exitCode = 1;
