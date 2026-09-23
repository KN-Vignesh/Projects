import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const portfolioUrl = process.env.PORTFOLIO_BASE_URL ?? 'http://127.0.0.1:4173';

const pages = [
  { name: 'home', route: '#/' },
  { name: 'projects', route: '#/?id=project-system' },
  { name: 'customer churn detail', route: '#/projects/customer-churn' },
  { name: 'VERO detail', route: '#/docs/VERO/README' },
  { name: 'contact', route: '#/?id=contact' },
];

for (const pageDefinition of pages) {
  test(`${pageDefinition.name} has no serious accessibility violations`, async ({ page }) => {
    await page.goto(`${portfolioUrl}/${pageDefinition.route}`, { waitUntil: 'domcontentloaded' });
    await expect(page.locator('.markdown-section')).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();

    const seriousViolations = results.violations.filter((violation) =>
      ['serious', 'critical'].includes(violation.impact ?? ''),
    );

    expect(seriousViolations, JSON.stringify(seriousViolations, null, 2)).toEqual([]);
  });
}