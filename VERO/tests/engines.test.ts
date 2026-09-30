import assert from 'node:assert/strict';
import { parseGitHubPrUrl } from '../src/server/github.js';
import { runSonarQubeAnalysis } from '../src/server/sonarEngine.js';
import { runDeterministicDecisionEngine } from '../src/server/decisionEngine.js';
import { runJevInference } from '../src/server/jevEngine.js';
import { PullRequestMetadata, PullRequestFile } from '../src/types.js';

console.log('--- Running Vero Engines Test Suite ---');

// 1. Test GitHub PR URL Parsing
{
  console.log('Test 1: parseGitHubPrUrl');
  const standard = parseGitHubPrUrl('https://github.com/facebook/react/pull/12345');
  assert.ok(standard, 'Standard GitHub URL should parse');
  assert.equal(standard.owner, 'facebook');
  assert.equal(standard.repo, 'react');
  assert.equal(standard.pullNumber, 12345);
  assert.equal(standard.canonicalUrl, 'https://github.com/facebook/react/pull/12345');

  const shorthand = parseGitHubPrUrl('KN-Vignesh/PR-Sentinel-Demo#1');
  assert.ok(shorthand, 'Shorthand URL should parse');
  assert.equal(shorthand.owner, 'KN-Vignesh');
  assert.equal(shorthand.repo, 'PR-Sentinel-Demo');
  assert.equal(shorthand.pullNumber, 1);

  const invalid = parseGitHubPrUrl('https://example.com/not-github');
  assert.equal(invalid, null, 'Non-GitHub URL should return null');
  console.log('✓ parseGitHubPrUrl passed all assertions');
}

// 2. Test SonarQube Static Analysis Engine
{
  console.log('Test 2: runSonarQubeAnalysis');
  const dirtyFiles: PullRequestFile[] = [
    {
      filename: 'src/api/auth.ts',
      status: 'modified',
      additions: 10,
      deletions: 2,
      changes: 12,
      patch: `@@ -1,4 +1,8 @@\n+const apiKey = "sk_live_1234567890abcdef";\n+const query = db.query(\`SELECT * FROM users WHERE id = \${userId}\`);\n+const pass = "password = 'supersecretstring'";`,
      isSecuritySensitive: true,
      isConfigFile: false,
      isTestFile: false,
      language: 'typescript',
    },
  ];

  const analysis = runSonarQubeAnalysis(dirtyFiles);
  assert.equal(analysis.qualityGate, 'FAILED', 'Quality Gate must fail on critical vulnerabilities');
  assert.ok(analysis.metrics.vulnerabilities >= 1, 'Should detect at least 1 vulnerability');
  assert.ok(analysis.issues.some((i) => i.ruleId === 'S2068'), 'Should detect S2068 (hardcoded credential)');
  assert.ok(analysis.issues.some((i) => i.ruleId === 'S3649'), 'Should detect S3649 (SQL concatenation)');

  const cleanFiles: PullRequestFile[] = [
    {
      filename: 'src/utils/math.ts',
      status: 'modified',
      additions: 5,
      deletions: 0,
      changes: 5,
      patch: `@@ -1,2 +1,7 @@\n+export function add(a: number, b: number): number {\n+  return a + b;\n+}`,
      isSecuritySensitive: false,
      isConfigFile: false,
      isTestFile: false,
      language: 'typescript',
    },
    {
      filename: 'tests/math.test.ts',
      status: 'added',
      additions: 6,
      deletions: 0,
      changes: 6,
      patch: `@@ -0,0 +1,6 @@\n+import { add } from '../src/utils/math';\n+test('add', () => { expect(add(1, 2)).toBe(3); });`,
      isSecuritySensitive: false,
      isConfigFile: false,
      isTestFile: true,
      language: 'typescript',
    },
  ];
  const cleanAnalysis = runSonarQubeAnalysis(cleanFiles);
  assert.equal(cleanAnalysis.qualityGate, 'PASSED', 'Clean files should pass Quality Gate');
  assert.equal(cleanAnalysis.metrics.vulnerabilities, 0);
  console.log('✓ runSonarQubeAnalysis passed all assertions');
}

// 3. Test Jev Probabilistic Inference Engine
{
  console.log('Test 3: runJevInference');
  const samplePr: PullRequestMetadata = {
    owner: 'test-org',
    repo: 'test-repo',
    number: 42,
    title: 'fix(security): sanitize sql parameters and update secret management',
    description: 'Fixes CVE vulnerability by parameterizing user input queries.',
    author: { login: 'security-bot', avatarUrl: '' },
    state: 'open',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    baseBranch: 'main',
    headBranch: 'security-patch',
    additions: 25,
    deletions: 15,
    changedFilesCount: 2,
    commitsCount: 1,
    url: 'https://github.com/test-org/test-repo/pull/42',
  };

  const sampleFiles: PullRequestFile[] = [
    {
      filename: 'src/db/auth.ts',
      status: 'modified',
      additions: 25,
      deletions: 15,
      changes: 40,
      patch: '+// fix: use parameterized query\n+const query = db.prepare("SELECT * FROM users WHERE id = ?");',
      isSecuritySensitive: true,
      isConfigFile: false,
      isTestFile: false,
      language: 'typescript',
    },
  ];

  const jev = await runJevInference(samplePr, sampleFiles);
  assert.ok(jev.category.selected, 'Category must be selected');
  assert.ok(jev.risk.selected, 'Risk level must be selected');
  assert.ok(jev.calibratedScore >= 0 && jev.calibratedScore <= 100, 'Score must be between 0 and 100');
  assert.ok(jev.category.entropy !== undefined && jev.category.entropy >= 0, 'Shannon entropy must be non-negative');
  console.log(`✓ runJevInference passed (category=${jev.category.selected}, risk=${jev.risk.selected}, score=${jev.calibratedScore})`);
}

// 4. Test Deterministic Decision Engine & Policy Hierarchy
{
  console.log('Test 4: runDeterministicDecisionEngine');
  const pr: PullRequestMetadata = {
    owner: 'acme',
    repo: 'api',
    number: 101,
    title: 'feat: add payment gateway',
    description: 'Integrates payment processor',
    author: { login: 'dev', avatarUrl: '' },
    state: 'open',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    baseBranch: 'main',
    headBranch: 'payment',
    additions: 200,
    deletions: 10,
    changedFilesCount: 3,
    commitsCount: 2,
    url: 'https://github.com/acme/api/pull/101',
  };

  const dirtyFiles: PullRequestFile[] = [
    {
      filename: 'src/payment.ts',
      status: 'modified',
      additions: 200,
      deletions: 10,
      changes: 210,
      patch: '+const key = "sk_live_9876543210123456";',
      isSecuritySensitive: true,
      isConfigFile: false,
      isTestFile: false,
      language: 'typescript',
    },
  ];

  const sonar = runSonarQubeAnalysis(dirtyFiles);
  const jev = await runJevInference(pr, dirtyFiles);
  const assessment = runDeterministicDecisionEngine(pr, dirtyFiles, sonar, jev);

  // Policy POL-01 requires security review and flags critical risk when vulnerability is detected
  assert.equal(assessment.verdict, 'SECURITY_REVIEW_REQUIRED', 'Verdict must be SECURITY_REVIEW_REQUIRED when vulnerability is detected');
  assert.equal(assessment.overallRisk, 'CRITICAL', 'Overall risk should be CRITICAL due to vulnerability');
  assert.ok(
    assessment.activePolicies.some((p) => p.id === 'POL-01-SEC-VULN'),
    'POL-01-SEC-VULN must be active'
  );
  assert.ok(assessment.recommendedActions.length > 0, 'Must provide recommended actions');
  assert.ok(assessment.confidencePercent > 0, 'Must compute confidence percent');

  console.log('✓ runDeterministicDecisionEngine passed all assertions');
}

console.log('--- ALL VERO ENGINE TESTS PASSED SUCCESSFULLY ---');
