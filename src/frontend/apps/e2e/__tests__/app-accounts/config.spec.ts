import { expect, test } from '@playwright/test';

import { CONFIG, overrideConfig } from './utils-common';

test.describe('Config', () => {
  if (process.env.IS_INSTANCE !== 'true') {
    test('it checks that sentry is trying to init from config endpoint', async ({
      page,
    }) => {
      await overrideConfig(page, {
        SENTRY_DSN: 'https://sentry.io/123',
      });

      const invalidMsg = 'Invalid Sentry Dsn: https://sentry.io/123';
      const consoleMessage = page.waitForEvent('console', {
        timeout: 5000,
        predicate: (msg) => msg.text().includes(invalidMsg),
      });

      await page.goto('/');

      expect((await consoleMessage).text()).toContain(invalidMsg);
    });
  }

  test('it checks FRONTEND_CSS_URL config', async ({ page }) => {
    await overrideConfig(page, {
      FRONTEND_CSS_URL: 'http://localhost:123465/css/style.css',
    });

    await page.goto('/');

    await expect(
      page
        .locator('head link[href="http://localhost:123465/css/style.css"]')
        .first(),
    ).toBeAttached();
  });

  test('it checks FRONTEND_JS_URL config', async ({ page }) => {
    await overrideConfig(page, {
      FRONTEND_JS_URL: 'http://localhost:123465/js/script.js',
    });

    await page.goto('/');

    await expect(
      page
        .locator('script[src="http://localhost:123465/js/script.js"]')
        .first(),
    ).toBeAttached();
  });

  if (process.env.IS_INSTANCE !== 'true') {
    test('it checks the config api is called', async ({ page }) => {
      const responsePromise = page.waitForResponse(
        (response) =>
          response.url().includes('/config/') && response.status() === 200,
      );

      await page.goto('/');

      const response = await responsePromise;
      expect(response.ok()).toBeTruthy();

      const json = (await response.json()) as typeof CONFIG;
      expect(json).toStrictEqual(CONFIG);
    });
  }
});

test.describe('Config: Not logged', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('it checks that theme is configured from config endpoint', async ({
    page,
  }) => {
    await page.goto('/');

    await expect(
      page.getByText('My Account, your gateway to the collaborative suite.'),
    ).toHaveCSS('font-family', /Roboto/i, {
      timeout: 10000,
    });

    await overrideConfig(page, {
      FRONTEND_THEME: 'dsfr',
    });

    await page.goto('/');

    await expect(
      page.getByText('My Account, your gateway to the collaborative suite.'),
    ).toHaveCSS('font-family', /Marianne/i, {
      timeout: 10000,
    });
  });
});
