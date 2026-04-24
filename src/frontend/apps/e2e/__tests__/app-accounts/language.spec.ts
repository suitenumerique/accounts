import { expect, test } from '@playwright/test';

import {
  TestLanguage,
  overrideConfig,
  waitForLanguageSwitch,
} from './utils-common';

test.describe('Language', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('it checks theme_customization.translations config', async ({
    page,
  }) => {
    await overrideConfig(page, {
      theme_customization: {
        translations: {
          en: {
            translation: {
              'My Account': 'My Custom Accounts',
            },
          },
        },
        header: {
          logo: {},
          icon: {
            withTitle: true,
          },
        },
      },
    });

    await page.goto('/');

    await expect(page.getByText('My Custom Accounts')).toBeAttached();
  });

  test('checks language switching', async ({ page }) => {
    const header = page.locator('header').first();
    const languagePicker = header.locator('.--accounts--language-picker-text');

    await expect(page.locator('html')).toHaveAttribute('lang', 'en-us');

    // initial language should be english
    const headerTitle = page.getByTestId('header-logo-link');
    await expect(headerTitle).toBeVisible();
    await expect(headerTitle).toContainText('My Account');

    // switch to french
    await waitForLanguageSwitch(page, TestLanguage.French);

    await expect(page.locator('html')).toHaveAttribute('lang', 'fr');

    await expect(
      header.getByRole('button').getByText('Français'),
    ).toBeVisible();

    await expect(headerTitle).toBeVisible();
    await expect(headerTitle).toContainText('Mon Compte');

    await expect(page.getByLabel('Se déconnecter')).toBeVisible();

    // Switch to German using the utility function for consistency
    await waitForLanguageSwitch(page, TestLanguage.German);
    await expect(header.getByRole('button').getByText('Deutsch')).toBeVisible();

    await expect(page.getByLabel('Abmelden')).toBeVisible();

    await expect(page.locator('html')).toHaveAttribute('lang', 'de');

    await languagePicker.click();

    await expect(page.locator('[role="menu"]')).toBeVisible();

    const menuItems = page.locator('[role="menuitemradio"]');
    await expect(menuItems.first()).toBeVisible();

    await menuItems.first().click();

    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(languagePicker).toContainText('English');
  });

  test('can switch language using only keyboard', async ({ page }) => {
    await page.goto('/');
    await waitForLanguageSwitch(page, TestLanguage.English);

    const languagePicker = page.getByRole('button', {
      name: /select language/i,
    });

    await expect(languagePicker).toBeVisible();

    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    await page.keyboard.press('Enter');

    const menu = page.getByRole('menu');
    await expect(menu).toBeVisible();

    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');

    await expect(page.locator('html')).not.toHaveAttribute('lang', 'en-us');
  });

  test('checks that backend uses the same language as the frontend', async ({
    page,
  }) => {
    // Helper function to intercept and assert 404 response
    const check404Response = async (expectedDetail: string) => {
      const interceptedBackendResponse = await page.request.get(
        `${process.env.BASE_API_URL}/404/`,
      );

      // Assert that the intercepted error message is in the expected language
      expect(await interceptedBackendResponse.json()).toStrictEqual({
        detail: expectedDetail,
      });
    };

    // Check for English 404 response
    await check404Response('Not found.');

    await waitForLanguageSwitch(page, TestLanguage.French);

    // Check for French 404 response
    await check404Response('Pas trouvé.');
  });
});
