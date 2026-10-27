'use client';

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useTranslation } from 'react-i18next';

import { useAuth } from '@/features/auth/Auth';
import { useConfig } from '@/features/config/ConfigProvider';

export interface VaultClientContextValue {
  /**
   * Runtime feature flag (ENCRYPTION_FEATURE_ENABLED on the backend, with both
   * service URLs set). When false the SDK script is never loaded and every
   * encryption entry point stays hidden.
   */
  isEnabled: boolean;
  /** The VaultClient, once initialized and given the user's auth context. */
  client: VaultClient | null;
  /** This device's encryption status, or null while it is not known yet. */
  status: EncryptionStatus | null;
  /** Set when the SDK could not be loaded or the vault did not answer. */
  error: string | null;
  /** Ask the vault for the status again (after an interface flow, a key change...). */
  refreshStatus: () => Promise<void>;
  /**
   * Load the SDK and the vault. Called by the encryption screen when it mounts,
   * so the other sections never pay for them; the client then stays alive.
   */
  start: () => void;
}

const VaultClientContext = createContext<VaultClientContextValue>({
  isEnabled: false,
  client: null,
  status: null,
  error: null,
  refreshStatus: async () => {},
  start: () => {},
});

export const useVaultClient = () => useContext(VaultClientContext);

const clientScriptUrl = (vaultUrl: string) =>
  `${vaultUrl.replace(/\/+$/, '')}/client.js`;

/** Load the client SDK from the vault domain, once per page. */
export const loadClientScript = (vaultUrl: string): Promise<void> =>
  new Promise((resolve, reject) => {
    if (window.EncryptionClient?.VaultClient) {
      resolve();
      return;
    }

    const src = clientScriptUrl(vaultUrl);
    const onError = () =>
      reject(new Error('Failed to load the encryption client SDK'));
    const existing = document.querySelector<HTMLScriptElement>(
      `script[src="${src}"]`,
    );

    if (existing) {
      existing.addEventListener('load', () => resolve());
      existing.addEventListener('error', onError);
      return;
    }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = onError;
    document.head.appendChild(script);
  });

export const VaultClientProvider = ({ children }: { children: ReactNode }) => {
  const { config } = useConfig();
  const { user } = useAuth();
  const { i18n } = useTranslation();

  const vaultUrl = config.ENCRYPTION_VAULT_URL || null;
  const interfaceUrl = config.ENCRYPTION_INTERFACE_URL || null;
  const isEnabled =
    config.ENCRYPTION_FEATURE_ENABLED === true && !!vaultUrl && !!interfaceUrl;
  // The products know this user by the `sub` claim Accounts issues them, so the
  // vault must be keyed by that same value to share keys with them.
  const suiteUserId = user?.sub ?? null;

  const clientRef = useRef<VaultClient | null>(null);
  const [client, setClient] = useState<VaultClient | null>(null);
  const [status, setStatus] = useState<EncryptionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStarted, setIsStarted] = useState(false);
  const start = useCallback(() => setIsStarted(true), []);

  const refreshStatus = useCallback(async () => {
    const current = clientRef.current;
    if (!current) {
      return;
    }

    try {
      setStatus(await current.getEncryptionStatus());
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, []);

  useEffect(() => {
    if (
      !isStarted ||
      !isEnabled ||
      !vaultUrl ||
      !interfaceUrl ||
      !suiteUserId
    ) {
      return;
    }

    let destroyed = false;
    let instance: VaultClient | null = null;

    const init = async () => {
      try {
        await loadClientScript(vaultUrl);
        const sdk = window.EncryptionClient;
        if (destroyed || !sdk) {
          return;
        }

        instance = new sdk.VaultClient({
          vaultUrl,
          interfaceUrl,
          theme: config.FRONTEND_THEME || 'default',
          lang: i18n.language,
        });

        const onKeysChanged = () => void refreshStatus();
        instance.on('onboarding:complete', onKeysChanged);
        instance.on('keys-changed', onKeysChanged);
        instance.on('keys-destroyed', onKeysChanged);

        await instance.init();
        if (destroyed) {
          return;
        }

        instance.setAuthContext({ suiteUserId });
        clientRef.current = instance;
        const initialStatus = await instance.getEncryptionStatus();
        if (destroyed) {
          return;
        }

        setStatus(initialStatus);
        setClient(instance);
      } catch (err) {
        if (!destroyed) {
          setError((err as Error).message);
        }
      }
    };

    void init();

    return () => {
      destroyed = true;
      instance?.destroy();
      clientRef.current = null;
      setClient(null);
      setStatus(null);
      setError(null);
    };
    // Theme and language are read once: re-creating the client (and its vault
    // iframe) on those changes is intentionally avoided.
  }, [
    isStarted,
    isEnabled,
    vaultUrl,
    interfaceUrl,
    suiteUserId,
    refreshStatus,
  ]);

  return (
    <VaultClientContext.Provider
      value={{ isEnabled, client, status, error, refreshStatus, start }}
    >
      {children}
    </VaultClientContext.Provider>
  );
};
