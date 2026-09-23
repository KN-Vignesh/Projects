import assert from 'node:assert/strict';
import test from 'node:test';
import { buildDryRunArtifacts } from '../../guardian/dry-run.js';

test('dry-run pipeline creates previews without enabling writes', async () => {
  const artifacts = await buildDryRunArtifacts();
  assert.equal(artifacts.policy.allowed, true);
  assert.match(artifacts.issuePreview, /NO GITHUB ISSUE CREATED/);
  assert.match(artifacts.prPreview, /PR NOT CREATED/);
  assert.equal(artifacts.branchPreview.status, 'simulated');
  assert.equal(artifacts.repairExecution.status, 'dry-run');
  assert.deepEqual(artifacts.repairExecution.filesChanged, []);
});

test('same synthetic failure produces the same fingerprint', async () => {
  const first = await buildDryRunArtifacts();
  const second = await buildDryRunArtifacts();
  assert.equal(first.fingerprint, second.fingerprint);
});
