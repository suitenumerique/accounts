import { test, expect } from "@playwright/test";

import { clearDb, login } from "./utils-common";

test("displays the welcome message once authenticated", async ({ page }) => {
  await clearDb();
  await login(page, "e2e@accounts.test");

  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Welcome on LaSuite Account" }),
  ).toBeVisible();
});
