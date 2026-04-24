import { Page, expect } from '@playwright/test';

import theme_customization from '../../../../../backend/accounts/configuration/theme/default.json';

export type BrowserName = 'chromium' | 'firefox' | 'webkit';
export const BROWSERS: BrowserName[] = ['chromium', 'webkit', 'firefox'];

export const CONFIG = {
  API_USERS_SEARCH_QUERY_MIN_LENGTH: 3,
  CRISP_WEBSITE_ID: null,
  ENVIRONMENT: 'development',
  FRONTEND_CSS_URL: null,
  FRONTEND_JS_URL: null,
  FRONTEND_HOMEPAGE_FEATURE_ENABLED: true,
  FRONTEND_SILENT_LOGIN_ENABLED: false,
  FRONTEND_THEME: null,
  MEDIA_BASE_URL: process.env.MEDIA_BASE_URL,
  LANGUAGES: [
    ['en-us', 'English'],
    ['fr-fr', 'Français'],
    ['de-de', 'Deutsch'],
    ['nl-nl', 'Nederlands'],
  ],
  LANGUAGE_CODE: 'en-us',
  POSTHOG_KEY: {},
  SENTRY_DSN: null,
  theme_customization,
} as const;

export const overrideConfig = async (
  page: Page,
  newConfig: { [_K in keyof typeof CONFIG]?: unknown },
) =>
  await page.route(/.*\/api\/v1.0\/config\/.*/, async (route) => {
    const request = route.request();
    if (request.method().includes('GET')) {
      await route.fulfill({
        json: {
          ...CONFIG,
          ...newConfig,
        },
      });
    } else {
      await route.continue();
    }
  });

export const getCurrentConfig = async (page: Page) => {
  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().includes('/config/') && response.status() === 200,
  );

  await page.goto('/');

  const response = await responsePromise;
  expect(response.ok()).toBeTruthy();

  return (await response.json()) as typeof CONFIG;
};

export const getOtherBrowserName = (browserName: BrowserName) => {
  const otherBrowserName = BROWSERS.find((b) => b !== browserName);
  if (!otherBrowserName) {
    throw new Error('No alternative browser found');
  }
  return otherBrowserName;
};

export const randomName = (name: string, browserName: string, length: number) =>
  Array.from({ length }, (_el, index) => {
    return `${browserName}-${Math.floor(Math.random() * 10000)}-${index}-${name}`;
  });

export const openHeaderMenu = async (page: Page) => {
  const toggleButton = page.getByTestId('header-menu-toggle');
  await expect(toggleButton).toBeVisible();

  const isExpanded =
    (await toggleButton.getAttribute('aria-expanded')) === 'true';
  if (!isExpanded) {
    await toggleButton.click();
  }
};

export const closeHeaderMenu = async (page: Page) => {
  const toggleButton = page.getByTestId('header-menu-toggle');
  await expect(toggleButton).toBeVisible();

  const isExpanded =
    (await toggleButton.getAttribute('aria-expanded')) === 'true';
  if (isExpanded) {
    await toggleButton.click();
  }
};

export const toggleHeaderMenu = async (page: Page) => {
  const toggleButton = page.getByTestId('header-menu-toggle');
  await expect(toggleButton).toBeVisible();
  await toggleButton.click();
};

// language helper
export const TestLanguage = {
  English: {
    label: 'English',
    expectedLocale: ['en-us'],
  },
  French: {
    label: 'Français',
    expectedLocale: ['fr-fr'],
  },
  German: {
    label: 'Deutsch',
    expectedLocale: ['de-de'],
  },
  Swedish: {
    label: 'Svenska',
    expectedLocale: ['sv-se'],
  },
} as const;

type TestLanguageKey = keyof typeof TestLanguage;
type TestLanguageValue = (typeof TestLanguage)[TestLanguageKey];

export async function waitForLanguageSwitch(
  page: Page,
  lang: TestLanguageValue,
) {
  await page.route(/\**\/api\/v1.0\/users\/\**/, async (route, request) => {
    if (request.method().includes('PATCH')) {
      await route.fulfill({
        json: {
          language: lang.expectedLocale[0],
        },
      });
    } else {
      await route.continue();
    }
  });

  const header = page.locator('header').first();
  const languagePicker = header.locator('.--accounts--language-picker-text');
  const isAlreadyTargetLanguage = await languagePicker
    .innerText()
    .then((text) => text.toLowerCase().includes(lang.label.toLowerCase()));

  if (isAlreadyTargetLanguage) {
    return;
  }

  await languagePicker.click();

  await page.getByRole('menuitemradio', { name: lang.label }).click();
}
