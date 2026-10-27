import { expect, test } from "@playwright/test";

import { clearDb, login } from "./utils-common";
import {
  VAULT_URL,
  closeEncryptionInterface,
  getEncryptionCalls,
  mockEncryptionService,
} from "./utils-encryption";

const EMAIL = "e2e-encryption@accounts.test";

test.beforeEach(async ({ page }) => {
  await clearDb();
  await login(page, EMAIL);
});

test("hides the encryption entry when the feature is off", async ({ page }) => {
  await mockEncryptionService(page, "active", { enabled: false });
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Personal information" }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Encryption" })).toHaveCount(0);
});

test("loads the encryption service only once its section opens", async ({
  page,
}) => {
  const sdkRequests: string[] = [];
  page.on("request", (request) => {
    if (request.url().startsWith(VAULT_URL)) {
      sdkRequests.push(request.url());
    }
  });
  await mockEncryptionService(page, "active");
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Personal information" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Security" }).click();
  expect(sdkRequests).toHaveLength(0);
  expect(await getEncryptionCalls(page)).toHaveLength(0);

  await page.getByRole("button", { name: "Encryption" }).click();
  await expect(
    page.getByText("Encryption is active on this device"),
  ).toBeVisible();
  expect(sdkRequests).toEqual([`${VAULT_URL}/client.js`]);
});

test("opens the section a product links to", async ({ page }) => {
  await mockEncryptionService(page, "active");
  await page.goto("/?section=encryption");

  await expect(
    page.getByText("Encryption is active on this device"),
  ).toBeVisible();
});

test("ignores a link to encryption while the feature is off, or to an unknown section", async ({
  page,
}) => {
  await mockEncryptionService(page, "active", { enabled: false });
  await page.goto("/?section=encryption");
  await expect(
    page.getByRole("heading", { name: "Personal information" }),
  ).toBeVisible();

  await page.goto("/?section=unknown");
  await expect(
    page.getByRole("heading", { name: "Personal information" }),
  ).toBeVisible();
});

test("keeps the chosen section in the address", async ({ page }) => {
  await mockEncryptionService(page, "active");
  await page.goto("/");
  await page.getByRole("button", { name: "Encryption" }).click();

  await expect(page).toHaveURL(/[?&]section=encryption\b/);
  await page.reload();
  await expect(
    page.getByText("Encryption is active on this device"),
  ).toBeVisible();
});

test("identifies the user to the vault by their OIDC sub", async ({ page }) => {
  await mockEncryptionService(page, "active");
  await page.goto("/");
  await page.getByRole("button", { name: "Encryption" }).click();
  await expect(
    page.getByText("Encryption is active on this device"),
  ).toBeVisible();

  const me = await (
    await page.request.get("http://localhost:9901/api/v1.0/users/me/")
  ).json();
  expect(await getEncryptionCalls(page)).toContainEqual([
    "setAuthContext",
    { suiteUserId: me.sub },
  ]);
});

test("opens each settings flow from the active page", async ({ page }) => {
  await mockEncryptionService(page, "active");
  await page.goto("/");
  await page.getByRole("button", { name: "Encryption" }).click();

  await expect(
    page.getByRole("heading", { name: "Encryption", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Encryption is active on this device"),
  ).toBeVisible();

  const flows: [string, string][] = [
    ["Manage", "manage"],
    ["Add a device", "add-device"],
    ["Show code", "verification-code"],
    ["Change recovery phrase", "recovery-phrase"],
    ["Manage trusted contacts", "trusted-contacts"],
  ];
  for (const [label, section] of flows) {
    await page.getByRole("button", { name: label, exact: true }).click();
    await expect
      .poll(() => getEncryptionCalls(page))
      .toContainEqual(["openSettings", section]);
    await closeEncryptionInterface(page);
  }
});

test("offers the setup when encryption is not set up on this device", async ({
  page,
}) => {
  await mockEncryptionService(page, "not-set-up");
  await page.goto("/");
  await page.getByRole("button", { name: "Encryption" }).click();

  await expect(
    page.getByText("Encryption isn't set up on this device"),
  ).toBeVisible();
  await expect(page.getByText("Your encryption settings")).toHaveCount(0);

  await page.getByRole("button", { name: "Set up" }).click();
  await expect
    .poll(() => getEncryptionCalls(page))
    .toContainEqual(["openOnboarding"]);
});

test("offers a review when encryption is off for the account", async ({
  page,
}) => {
  await mockEncryptionService(page, "disabled-for-account");
  await page.goto("/");
  await page.getByRole("button", { name: "Encryption" }).click();

  await expect(
    page.getByText("Encryption is off for your account"),
  ).toBeVisible();
  await expect(page.getByText("Your encryption settings")).toHaveCount(0);

  await page.getByRole("button", { name: "Review options" }).click();
  await expect
    .poll(() => getEncryptionCalls(page))
    .toContainEqual(["openSettings", "manage"]);
});

test("reads the status again once the interface closes", async ({ page }) => {
  await mockEncryptionService(page, "active");
  await page.goto("/");
  await page.getByRole("button", { name: "Encryption" }).click();
  await expect(
    page.getByText("Encryption is active on this device"),
  ).toBeVisible();

  // The flow destroyed the keys inside the interface.
  await page.getByRole("button", { name: "Manage", exact: true }).click();
  await expect
    .poll(() => getEncryptionCalls(page))
    .toContainEqual(["openSettings", "manage"]);
  await page.evaluate(() => {
    (window as unknown as { __encryptionState: string }).__encryptionState =
      "not-set-up";
  });
  await closeEncryptionInterface(page);

  await expect(
    page.getByText("Encryption isn't set up on this device"),
  ).toBeVisible();
});
