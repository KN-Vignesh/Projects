import { expect, test } from '@playwright/test';

const portfolioUrl = process.env.PORTFOLIO_BASE_URL ?? 'http://127.0.0.1:4173';

test('portfolio home loads without runtime or network failures', async ({ page }) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];
  const failedRequests: string[] = [];
  const unsuccessfulResponses: string[] = [];

  page.on('console', (message) => {
    if (message.type() === 'error') {
      consoleErrors.push(message.text());
    }
  });

  page.on('pageerror', (error) => {
    pageErrors.push(error.message);
  });

  page.on('requestfailed', (request) => {
    failedRequests.push(`${request.method()} ${request.url()} - ${request.failure()?.errorText ?? 'unknown error'}`);
  });

  page.on('response', (response) => {
    if (response.status() >= 400) {
      unsuccessfulResponses.push(`${response.status()} ${response.request().method()} ${response.url()}`);
    }
  });

  const response = await page.goto(portfolioUrl, { waitUntil: 'domcontentloaded' });

  expect(response, 'the portfolio homepage should return an HTTP response').not.toBeNull();
  expect(response?.status(), 'the portfolio homepage should return a successful status').toBeLessThan(400);

  const markdownSection = page.locator('.markdown-section');
  await expect(markdownSection).toBeVisible();

  await expect(page).toHaveTitle(/Vignesh K N/i);
  await expect(markdownSection.getByRole('heading', { level: 1 })).toContainText(
    'VIGNESH K N',
  );
  await expect(page.locator('.app-nav, .sidebar-nav').first()).toBeVisible();
  await expect(markdownSection.getByRole('heading', { name: /02.*PROJECT SYSTEM/i })).toBeVisible();
  await expect(markdownSection.getByRole('heading', { name: /05.*CONTACT/i })).toBeVisible();

  await expect(page.locator('a[href="#/projects/customer-churn"]')).toBeVisible();
  await expect(page.locator('a[href="https://github.com/KN-Vignesh/Projects"]')).toBeVisible();
  await expect(page.locator('a[href="https://www.linkedin.com/in/vignesh-k-n/"]')).toBeVisible();

  expect(pageErrors, 'the page should not emit uncaught JavaScript errors').toEqual([]);
  expect(consoleErrors, 'the page should not emit JavaScript console errors').toEqual([]);
  expect(failedRequests, 'the page should not contain failed network requests').toEqual([]);
  expect(unsuccessfulResponses, 'the page should not contain failed HTTP responses').toEqual([]);
});
