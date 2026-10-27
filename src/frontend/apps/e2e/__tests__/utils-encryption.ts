import { Page } from "@playwright/test";

export const VAULT_URL = "https://data.encryption.e2e.test";
export const INTERFACE_URL = "https://encryption.e2e.test";

export type EncryptionState =
  | "active"
  | "disabled-for-account"
  | "not-set-up"
  | "needs-attention";

/**
 * A stand-in for the encryption service's `client.js`, served in place of the
 * real one so the page can be tested without the encryption stack. It answers
 * the status from `window.__encryptionState`, records every call in
 * `window.__encryptionCalls`, and emits `interface:ready` right after any
 * open* call, the way the real interface does once its modal is on screen;
 * `window.__closeEncryptionInterface()` plays the user closing it.
 */
const FAKE_SDK = `
(() => {
  window.__encryptionCalls = [];
  class VaultClient {
    constructor(options) {
      this.listeners = {};
      window.__encryptionCalls.push(["constructor", options]);
      window.__closeEncryptionInterface = () => this.emit("interface:closed");
    }
    async init() {}
    destroy() {}
    setAuthContext(context) {
      window.__encryptionCalls.push(["setAuthContext", context]);
    }
    async getEncryptionStatus() {
      return { state: window.__encryptionState, registered: true };
    }
    on(event, listener) {
      (this.listeners[event] = this.listeners[event] || []).push(listener);
    }
    off(event, listener) {
      this.listeners[event] = (this.listeners[event] || []).filter((l) => l !== listener);
    }
    emit(event) {
      (this.listeners[event] || []).slice().forEach((listener) => listener());
    }
    openOnboarding() {
      window.__encryptionCalls.push(["openOnboarding"]);
      setTimeout(() => this.emit("interface:ready"), 0);
    }
    openSettings(section) {
      window.__encryptionCalls.push(["openSettings", section]);
      setTimeout(() => this.emit("interface:ready"), 0);
    }
    closeInterface() {}
  }
  window.EncryptionClient = { VaultClient };
})();
`;

/**
 * Turns the encryption feature on in the configuration the frontend reads, and
 * serves the fake SDK from the vault URL.
 */
export const mockEncryptionService = async (
  page: Page,
  state: EncryptionState,
  { enabled = true }: { enabled?: boolean } = {},
) => {
  await page.addInitScript((initialState) => {
    (window as unknown as { __encryptionState: string }).__encryptionState =
      initialState;
  }, state);

  await page.route("**/api/v1.0/config/", async (route) => {
    const response = await route.fetch();
    const config = await response.json();
    await route.fulfill({
      response,
      json: {
        ...config,
        ENCRYPTION_FEATURE_ENABLED: enabled,
        ENCRYPTION_VAULT_URL: VAULT_URL,
        ENCRYPTION_INTERFACE_URL: INTERFACE_URL,
      },
    });
  });

  await page.route(`${VAULT_URL}/client.js`, (route) =>
    route.fulfill({ contentType: "text/javascript", body: FAKE_SDK }),
  );
};

export const getEncryptionCalls = (page: Page) =>
  page.evaluate(
    () =>
      (window as unknown as { __encryptionCalls?: unknown[][] })
        .__encryptionCalls ?? [],
  );

/** Play the user closing the encryption interface's modal. */
export const closeEncryptionInterface = (page: Page) =>
  page.evaluate(() =>
    (
      window as unknown as { __closeEncryptionInterface: () => void }
    ).__closeEncryptionInterface(),
  );
