import { test, expect } from "@playwright/test";

import { clearDb, login } from "./utils-common";

test("displays the account page once authenticated", async ({ page }) => {
  await clearDb();
  await login(page, "e2e@accounts.test");

  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Personal information" }),
  ).toBeVisible();
  await expect(page.getByText("My account")).toBeVisible();
});
