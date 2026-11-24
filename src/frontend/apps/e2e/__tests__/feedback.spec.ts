import { Page, expect, test } from '@playwright/test';

import { clearDb, login } from './utils-common';

const FEEDBACK_FORM_URL = 'https://forms.example.test/feedback';

const overrideFeedbackFormUrl = (page: Page, url: string | null) =>
  page.route('**/api/v1.0/config/', async (route) => {
    const response = await route.fetch();
    const config = await response.json();
    await route.fulfill({
      response,
      json: { ...config, FRONTEND_FEEDBACK_FORM_URL: url },
    });
  });

test.beforeEach(async ({ page }) => {
  await clearDb();
  await login(page, 'e2e-feedback@accounts.test');
});

test('keeps the help menu without a feedback form', async ({ page }) => {
  await overrideFeedbackFormUrl(page, null);
  await page.goto('/');

  await expect(page.locator('.suite__footer__help')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Give feedback' })).toHaveCount(
    0,
  );
});

test('replaces the help menu with a link to the feedback form', async ({
  page,
}) => {
  await overrideFeedbackFormUrl(page, FEEDBACK_FORM_URL);
  await page.goto('/');

  const link = page.getByRole('link', { name: 'Give feedback' });
  await expect(link).toHaveAttribute('href', FEEDBACK_FORM_URL);
  await expect(link).toHaveAttribute('target', '_blank');
  await expect(page.locator('.suite__footer__help')).toHaveCount(0);
});
