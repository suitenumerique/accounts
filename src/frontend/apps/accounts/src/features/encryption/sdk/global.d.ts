// Ambient bindings for the encryption service's VaultClient SDK.
//
// The full method/type surface lives in ./client-sdk.d.ts, a VERBATIM copy of
// the encryption service's generated declaration (served at
// <encryption-domain>/public-assets/client.d.ts). Regenerate it with:
//   curl http://encryption.localhost:7200/public-assets/client.d.ts -o client-sdk.d.ts
// Never hand-edit client-sdk.d.ts: fix signatures at the source and re-vendor.
export {};

declare global {
  type VaultClient = import('./client-sdk').VaultClient;
  type EncryptionStatus = import('./client-sdk').EncryptionStatus;
  type EncryptionSettingsSection = import('./client-sdk').SettingsSection;

  interface Window {
    EncryptionClient?: typeof import('./client-sdk');
  }
}
