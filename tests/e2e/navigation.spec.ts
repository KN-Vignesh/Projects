import { expect, test, type Page } from '@playwright/test';

const portfolioUrl = process.env.PORTFOLIO_BASE_URL ?? 'http://127.0.0.1:4173';

async function waitForPortfolioPage(page: Page) {
  await expect(page.locator('.markdown-section')).toBeVisible();
}

test('portfolio sections navigate through real hash links', async ({ page }) => {
  await page.goto(`${portfolioUrl}/#/`, { waitUntil: 'domcontentloaded' });
  await waitForPortfolioPage(page);

  await expect(page.locator('.markdown-section h1').first()).toContainText('VIGNESH K N');

  await page.getByRole('link', { name: '02 PROJECTS' }).click();
  await expect(page).toHaveURL(/#\/README\?id=project-system/);
  await expect(page.getByRole('heading', { name: /02.*PROJECT SYSTEM/i })).toBeVisible();

  await page.getByRole('link', { name: /open project/i }).first().click();
  await expect(page).toHaveURL(/#\/projects\/customer-churn/);
  await expect(page.locator('.markdown-section h1').first()).toContainText(
    'INTELLIGENT CUSTOMER CHURN PREDICTION',
  );

  await page.goBack();
  await expect(page).toHaveURL(/#\/README\?id=project-system/);
  await expect(page.getByRole('heading', { name: /02.*PROJECT SYSTEM/i })).toBeVisible();

  await page.locator('a[href="#/docs/VERO/README"]').click();
  await expect(page).toHaveURL(/#\/docs\/VERO\/README/);
  await expect(page.locator('.markdown-section h1').first()).toHaveText('VERO');

  await page.goBack();
  await expect(page).toHaveURL(/#\/README\?id=project-system/);
  await expect(page.getByRole('heading', { name: /02.*PROJECT SYSTEM/i })).toBeVisible();

  await page.getByRole('link', { name: 'VIGNESH K N' }).click();
  await expect(page).toHaveURL(/#\/$/);
  await expect(page.locator('.markdown-section h1').first()).toContainText('VIGNESH K N');

  await page.goBack();
  await expect(page).toHaveURL(/#\/README\?id=project-system/);
  await expect(page.getByRole('heading', { name: /02.*PROJECT SYSTEM/i })).toBeVisible();

  await page.goForward();
  await expect(page).toHaveURL(/#\/$/);
  await expect(page.locator('.markdown-section h1').first()).toContainText('VIGNESH K N');
});

test('portfolio section links resolve to the existing information architecture', async ({ page }) => {
  await page.goto(`${portfolioUrl}/#/`, { waitUntil: 'domcontentloaded' });
  await waitForPortfolioPage(page);

  const sectionLinks = [
    { label: '01 ABOUT', heading: /01.*ENGINEERING SYSTEM/i },
    { label: '02 PROJECTS', heading: /02.*PROJECT SYSTEM/i },
    { label: '03 AI STACK', heading: /03.*AI ENGINEERING STACK/i },
    { label: '04 LEARNING', heading: /04.*LEARNING SYSTEM/i },
    { label: '05 CONTACT', heading: /05.*CONTACT/i },
  ];

  for (const section of sectionLinks) {
    await page.getByRole('link', { name: section.label }).click();
    await expect(page.getByRole('heading', { name: section.heading })).toBeVisible();
  }
});