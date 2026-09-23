import { expect, test } from '@playwright/test';

const productionUrl = process.env.PORTFOLIO_URL;

test('deployed portfolio is reachable and healthy', async ({ page }) => {
  test.skip(!productionUrl, 'PORTFOLIO_URL is required for production smoke tests');

  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedRequests: string[] = [];
  const unsuccessfulResponses: string[] = [];

  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrors.push(message.text());
  });
  page.on('pageerror', (error) => pageErrors.push(error.message));
  page.on('requestfailed', (request) => {
    failedRequests.push(`${request.method()} ${request.url()}`);
  });
  page.on('response', (response) => {
    if (response.status() >= 400) {
      unsuccessfulResponses.push(`${response.status()} ${response.url()}`);
    }
  });

  const response = await page.goto(productionUrl!, { waitUntil: 'domcontentloaded' });

  expect(response).not.toBeNull();
  expect(response?.status()).toBeLessThan(400);
  await expect(page).toHaveTitle(/Vignesh K N/i);
  await expect(page.locator('.markdown-section')).toBeVisible();
  await expect(page.locator('.markdown-section h1').first()).toContainText('VIGNESH K N');
  await expect(page.locator('.app-nav, .sidebar-nav').first()).toBeVisible();
  await expect(page.locator('a[href="#/projects/customer-churn"]')).toBeVisible();
  await expect(page.locator('a[href="https://github.com/KN-Vignesh/Projects"]')).toBeVisible();
  await expect(page.locator('a[href="https://www.linkedin.com/in/vignesh-k-n/"]')).toBeVisible();

  expect(pageErrors, 'production should not emit uncaught page errors').toEqual([]);
  expect(consoleErrors, 'production should not emit console errors').toEqual([]);
  expect(failedRequests, 'production should not contain failed requests').toEqual([]);
  expect(unsuccessfulResponses, 'production should not contain HTTP errors').toEqual([]);
});