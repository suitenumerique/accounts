import { test, expect } from "@playwright/test";

import { keycloakSubmitCredentials } from "./utils-common";

/**
 * When the identity provider fails, the user lands on the login error page.
 * Retrying from there must bring them back to where they came from.
 */
test("retries the sign-in after an identity provider error", async ({
  page,
  baseURL,
}, testInfo) => {
  const nextUrl = `${baseURL}/?product=docs`;

  // The identity provider answers the first sign-in with an error. Playwright
  // does not route requests issued by a redirect, and WebKit cannot fulfill a
  // route with a redirect status, so the redirect to the identity provider is
  // replaced by a page that navigates to the error callback.
  await page.route(
    "**/api/v1.0/login/?**",
    async (route) => {
      const response = await route.fetch({ maxRedirects: 0 });
      const authorizeUrl = new URL(response.headers()["location"]);
      const callbackUrl = new URL(authorizeUrl.searchParams.get("redirect_uri")!);
      callbackUrl.searchParams.set("error", "server_error");
      callbackUrl.searchParams.set("state", authorizeUrl.searchParams.get("state")!);

      await route.fulfill({
        status: 200,
        contentType: "text/html",
        headers: { "set-cookie": response.headers()["set-cookie"] },
        body: `<meta http-equiv="refresh" content="0;url=${callbackUrl}">`,
      });
    },
    { times: 1 },
  );

  await page.goto(`/?next=${encodeURIComponent(nextUrl)}`);
  await page
    .getByRole("textbox", { name: "Email address" })
    .fill(`user-e2e-${testInfo.project.name}@accounts.test`);
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/login-error\/$/);
  await expect(
    page.getByRole("heading", { name: "Sign-in failed" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Try again" }).click();
  await keycloakSubmitCredentials(page, testInfo.project.name);

  await expect(page).toHaveURL(nextUrl);
  await expect(
    page.getByRole("heading", { name: "Personal information" }),
  ).toBeVisible();
});
