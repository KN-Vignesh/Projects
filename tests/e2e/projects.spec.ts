import { expect, test } from '@playwright/test';
import { portfolioProjects } from './project-config';

const portfolioUrl = process.env.PORTFOLIO_BASE_URL ?? 'http://127.0.0.1:4173';

for (const project of portfolioProjects) {
  test(`${project.name} project page is complete`, async ({ page }) => {
    await page.goto(`${portfolioUrl}/${project.route}`, { waitUntil: 'domcontentloaded' });

    const markdownSection = page.locator('.markdown-section');
    await expect(markdownSection).toBeVisible();
    await expect(markdownSection.locator('h1').first()).toHaveText(project.title);
    await expect(markdownSection.getByText(project.description).first()).toBeVisible();

    for (const section of project.requiredSections) {
      await expect(markdownSection.getByRole('heading', { name: section })).toBeVisible();
    }

    await expect(page.locator(`a[href="${project.githubHref}"]`).first()).toBeVisible();
  });
}