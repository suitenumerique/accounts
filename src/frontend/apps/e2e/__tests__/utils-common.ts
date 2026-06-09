import { exec } from "child_process";
import path from "path";

import { Page, expect } from "@playwright/test";

// repo root from __tests__/utils-common.ts: e2e -> apps -> frontend -> src -> root
const ROOT_PATH = path.join(__dirname, "/../../../../..");

/**
 * Performs a full Keycloak sign-in starting from the accounts home page.
 *
 * A dedicated user exists per browser in the `accounts` realm so the projects
 * can run without sharing a session:
 *   user-e2e-<browser> / password-e2e-<browser>
 */
export const keycloakSignIn = async (page: Page, browserName: string) => {
  // From the home page, go to Keycloak.
  await page.getByRole("button", { name: "Login" }).click();

  // We are now on the Keycloak login form of the `accounts` realm.
  await expect(page.locator("#username")).toBeVisible();

  if (await page.getByLabel("Restart login").isVisible()) {
    await page.getByLabel("Restart login").click();
  }

  await page.locator("#username").fill(`user-e2e-${browserName}`);
  await page.locator("#password").fill(`password-e2e-${browserName}`);
  await page.locator("#kc-login").click();
};

/**
 * Logs a user in by hitting the backend e2e endpoint, bypassing Keycloak.
 * Requires the backend to run with LOAD_E2E_URLS enabled (see `make
 * run-backend-e2e`). The session cookie it sets is reused by `page` next.
 */
export const login = async (page: Page, email: string) => {
  await page.request.post("http://localhost:9901/api/v1.0/e2e/user-auth/", {
    data: { email },
  });
};

const runTarget = (target: string) =>
  new Promise<void>((resolve, reject) => {
    exec(`cd ${ROOT_PATH} && make ${target}`, (error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });

/** Truncates the e2e database (via `make clear-db-e2e`). */
export const clearDb = async () => {
  await runTarget("clear-db-e2e");
};
