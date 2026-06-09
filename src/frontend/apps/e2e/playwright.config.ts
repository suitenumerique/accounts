import { defineConfig, devices } from "@playwright/test";

/**
 * The accounts stack (backend, Keycloak, frontend) is expected to be up and
 * serving the frontend at BASE_URL — locally via `make run` (or `make
 * run-frontend-development`) and in CI via `make bootstrap-e2e`.
 *
 * See https://playwright.dev/docs/test-configuration.
 */
const baseURL = process.env.BASE_URL || "http://localhost:9900";

export default defineConfig({
  timeout: 30 * 1000,
  testDir: "./__tests__",
  outputDir: "./test-results",

  fullyParallel: false,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests. */
  workers: 1,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [["html", { outputFolder: "./report", open: "never" }], ["list"]],

  use: {
    baseURL,
    viewport: { width: 1280, height: 720 },
    trace: "retain-on-failure",
    video: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        locale: "en-US",
        timezoneId: "Europe/Paris",
      },
    },
    {
      name: "webkit",
      use: {
        ...devices["Desktop Safari"],
        locale: "en-US",
        timezoneId: "Europe/Paris",
      },
    },
    {
      name: "firefox",
      use: {
        ...devices["Desktop Firefox"],
        locale: "en-US",
        timezoneId: "Europe/Paris",
      },
    },
  ],
});