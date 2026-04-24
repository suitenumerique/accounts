import { expect, test } from '@playwright/test';

import { overrideConfig } from './utils-common';

test.describe('Home page', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('checks all the elements are visible', async ({ page }) => {
    await page.goto('/');

    // Check header content
    const header = page.locator('header').first();
    const footer = page.locator('footer').first();
    await expect(header).toBeVisible();

    const languageButton = page.getByRole('button', {
      name: /Language|Select language/,
    });
    await expect(languageButton).toBeVisible();

    await expect(header.getByTestId('header-icon-docs')).toBeVisible();

    // Check the titles
    const h2 = page.locator('h2');
    await expect(h2.getByText('Govs ❤️ Open Source.')).toBeVisible();
    await expect(
      page.getByText(
        'My Account is the entry point to La Suite collaborative tools.',
      ),
    ).toBeVisible();
    await expect(
      page.getByRole('link', {
        name: 'Django Rest Framework',
      }),
    ).toHaveAttribute('href', 'https://www.django-rest-framework.org/');
    await expect(
      page.getByText('You can easily self-host My Account'),
    ).toBeVisible();
    await expect(
      page
        .getByRole('link', {
          name: 'licence',
        })
        .first(),
    ).toHaveAttribute(
      'href',
      'https://github.com/suitenumerique/accounts/blob/main/LICENSE',
    );
    await expect(
      h2.getByText('My Account, your gateway to the collaborative suite.'),
    ).toBeVisible();
    await expect(
      page.getByText(
        'Login to La Suite collaborative tools from one place. Soon, you will also be able to manage your account information here.',
      ),
    ).toBeVisible();
    await expect(
      page
        .getByRole('button', { name: process.env.SIGN_IN_EL_TRIGGER })
        .first(),
    ).toBeVisible();

    await expect(footer).toBeVisible();
  });

  test('checks all the elements are visible with dsfr theme', async ({
    page,
  }) => {
    await overrideConfig(page, {
      FRONTEND_THEME: 'dsfr',
      theme_customization: {
        footer: {
          default: {
            externalLinks: [
              {
                label: 'legifrance.gouv.fr',
                href: '#',
              },
            ],
          },
        },
        header: {
          logo: {
            src: '/assets/logo-gouv.svg',
            alt: 'Gouvernement Logo',
            style: { width: '110px', height: 'auto' },
          },
          icon: {
            src: '/assets/icon-docs-dsfr-v2.png',
            style: {
              width: '100px',
              height: 'auto',
            },
            alt: '',
            withTitle: false,
          },
        },
        home: {
          'with-proconnect': true,
          'icon-banner': {
            src: '/assets/icon-docs.svg',
            style: {
              width: '64px',
              height: 'auto',
            },
            alt: '',
          },
        },
      },
    });

    await page.goto('/');

    // Check header content
    const header = page.locator('header').first();
    const footer = page.locator('footer').first();
    await expect(header).toBeVisible({
      timeout: 10000,
    });

    // Check for language picker - it should be visible on desktop
    // Use a more flexible selector that works with both Header and HomeHeader
    const languageButton = page.getByRole('button', {
      name: /Language|Select language/,
    });
    await expect(languageButton).toBeVisible();

    await expect(
      header.getByRole('img', { name: 'Gouvernement Logo' }),
    ).toBeVisible();
    await expect(header.getByTestId('header-icon-docs')).toBeVisible();

    // Check the titles
    const h2 = page.locator('h2');
    await expect(h2.getByText('Govs ❤️ Open Source.')).toBeVisible();
    await expect(
      h2.getByText('My Account, your gateway to the collaborative suite.'),
    ).toBeVisible();
    await expect(
      page.getByText(
        'Login to La Suite collaborative tools from one place. Soon, you will also be able to manage your account information here.',
      ),
    ).toBeVisible();

    await expect(
      page.getByText(
        'My Account is already available, log in to access La Suite collaborative tools.',
      ),
    ).toBeVisible();
    await expect(
      page.getByRole('button', { name: 'Proconnect Login' }),
    ).toHaveCount(2);

    await expect(footer).toBeVisible();
  });

  test('it checks the homepage feature flag', async ({ page }) => {
    await overrideConfig(page, {
      FRONTEND_HOMEPAGE_FEATURE_ENABLED: false,
    });

    await page.goto('/');

    // Keyclock login page
    await expect(
      page
        .locator(`${process.env.SIGN_IN_EL_LOGIN_PAGE}`)
        .getByText('accounts'),
    ).toBeVisible();
  });
});
