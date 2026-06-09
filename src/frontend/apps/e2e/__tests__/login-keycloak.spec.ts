import { test, expect } from "@playwright/test";

import { keycloakSignIn } from "./utils-common";

/**
 * Smoke test for the real OIDC flow: it goes through the Keycloak login form
 * (no bypass) and checks the authenticated home page renders.
 */
test("signs in through Keycloak and shows the welcome message", async ({
  page,
}, testInfo) => {
  await page.goto("/");

  await keycloakSignIn(page, testInfo.project.name);

  await expect(
    page.getByRole("heading", { name: "Welcome on LaSuite Account" }),
  ).toBeVisible();
});
