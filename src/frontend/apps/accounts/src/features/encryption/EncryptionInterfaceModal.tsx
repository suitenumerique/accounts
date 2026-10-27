'use client';

import { Modal, ModalSize } from '@gouvfr-lasuite/cunningham-react';
import { Spinner } from '@gouvfr-lasuite/ui-kit';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';

import { useVaultClient } from './VaultClientProvider';

/** Which flow of the encryption interface to open. */
export type EncryptionFlow =
  | { kind: 'onboarding' }
  | { kind: 'settings'; section: EncryptionSettingsSection };

type EncryptionInterfaceModalProps = {
  flow: EncryptionFlow;
  onClose: () => void;
};

/**
 * Opens a flow of the encryption interface and stands in for it until it is on
 * screen. The interface draws its own modal over the page (and asks the user to
 * sign in to the encryption service itself when needed), so Accounts only shows
 * a loader until `interface:ready`, then unmounts on `interface:closed`.
 */
export const EncryptionInterfaceModal = ({
  flow,
  onClose,
}: EncryptionInterfaceModalProps) => {
  const { t } = useTranslation();
  const { client, refreshStatus } = useVaultClient();
  const [ready, setReady] = useState(false);
  const openedRef = useRef(false);

  useEffect(() => {
    if (!client) {
      return;
    }

    const handleReady = () => setReady(true);
    const handleClosed = () => {
      void refreshStatus();
      onClose();
    };

    client.on('interface:ready', handleReady);
    client.on('interface:closed', handleClosed);

    // Subscribed first, so an interface that comes up at once is not missed.
    if (!openedRef.current) {
      openedRef.current = true;
      if (flow.kind === 'onboarding') {
        client.openOnboarding();
      } else {
        client.openSettings(flow.section);
      }
    }

    return () => {
      client.off('interface:ready', handleReady);
      client.off('interface:closed', handleClosed);
    };
  }, [client, flow, onClose, refreshStatus]);

  // Nothing is at stake before the interface is on screen, so closing the
  // loader tears the frame down outright.
  const handleClose = useCallback(() => {
    client?.closeInterface();
    onClose();
  }, [client, onClose]);

  return (
    <Modal
      isOpen={!ready}
      closeOnClickOutside={false}
      onClose={handleClose}
      size={ModalSize.SMALL}
      aria-label={t('Encryption')}
    >
      <div className="encryption-interface-loader">
        <Spinner size="lg" />
      </div>
    </Modal>
  );
};
