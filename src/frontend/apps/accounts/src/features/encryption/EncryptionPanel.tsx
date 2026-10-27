'use client';

import { Button } from '@gouvfr-lasuite/cunningham-react';
import { Spinner } from '@gouvfr-lasuite/ui-kit';
import {
  Eye,
  PhoneDesktop,
  ShieldAlert,
  ShieldCheck,
  ShieldOff,
} from '@gouvfr-lasuite/ui-kit/icons';
import { ReactNode, useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import {
  EncryptionFlow,
  EncryptionInterfaceModal,
} from './EncryptionInterfaceModal';
import { useVaultClient } from './VaultClientProvider';

type BannerTone = 'success' | 'warning' | 'neutral';

type StatusBannerProps = {
  tone: BannerTone;
  icon: ReactNode;
  label: string;
  action?: ReactNode;
};

const StatusBanner = ({ tone, icon, label, action }: StatusBannerProps) => (
  <div className={`encryption-status encryption-status--${tone}`} role="status">
    <span className="encryption-status__icon" aria-hidden="true">
      {icon}
    </span>
    <p className="encryption-status__label">{label}</p>
    {action}
  </div>
);

type SettingRowProps = {
  title: string;
  description: string;
  action: ReactNode;
};

const SettingRow = ({ title, description, action }: SettingRowProps) => (
  <li className="encryption-setting">
    <div className="encryption-setting__text">
      <p className="encryption-setting__title">{title}</p>
      <p className="encryption-setting__description">{description}</p>
    </div>
    {action}
  </li>
);

export const EncryptionPanel = () => {
  const { t } = useTranslation();
  const { client, status, error, start } = useVaultClient();
  const [flow, setFlow] = useState<EncryptionFlow | null>(null);
  // Every request mounts a fresh host modal, which opens its flow exactly once.
  const [flowId, setFlowId] = useState(0);
  const closeFlow = useCallback(() => setFlow(null), []);

  useEffect(() => start(), [start]);

  const startFlow = (next: EncryptionFlow) => {
    setFlowId((id) => id + 1);
    setFlow(next);
  };
  const openSettings = (section: EncryptionSettingsSection) =>
    startFlow({ kind: 'settings', section });

  const renderBanner = () => {
    if (error && !status) {
      return (
        <StatusBanner
          tone="neutral"
          icon={<ShieldOff size={24} />}
          label={t('The encryption service could not be reached')}
          action={
            <Button
              size="nano"
              color="neutral"
              variant="bordered"
              onClick={() => window.location.reload()}
            >
              {t('Retry')}
            </Button>
          }
        />
      );
    }

    // Until the vault answers, no state is shown: a wrong banner would be worse
    // than a short wait.
    if (!client || !status) {
      return (
        <div
          className="encryption-status encryption-status--loading"
          role="status"
          aria-label={t('Loading encryption status')}
        >
          <Spinner size="sm" />
        </div>
      );
    }

    switch (status.state) {
      case 'active':
        return (
          <StatusBanner
            tone="success"
            icon={<ShieldCheck size={24} />}
            label={t('Encryption is active on this device')}
            action={
              <Button
                size="nano"
                color="success"
                variant="secondary"
                onClick={() => openSettings('manage')}
              >
                {t('Manage')}
              </Button>
            }
          />
        );
      case 'disabled-for-account':
        return (
          <StatusBanner
            tone="warning"
            icon={<ShieldAlert size={24} />}
            label={t('Encryption is off for your account')}
            action={
              <Button
                size="nano"
                color="warning"
                variant="secondary"
                onClick={() => openSettings('manage')}
              >
                {t('Review options')}
              </Button>
            }
          />
        );
      case 'needs-attention':
        return (
          <StatusBanner
            tone="warning"
            icon={<ShieldAlert size={24} />}
            label={t('Encryption needs your attention on this device')}
            action={
              <Button
                size="nano"
                color="warning"
                variant="secondary"
                onClick={() => openSettings('manage')}
              >
                {t('Review')}
              </Button>
            }
          />
        );
      case 'not-set-up':
      default:
        return (
          <StatusBanner
            tone="neutral"
            icon={<ShieldOff size={24} />}
            label={t("Encryption isn't set up on this device")}
            action={
              <Button
                size="nano"
                color="brand"
                variant="primary"
                onClick={() => startFlow({ kind: 'onboarding' })}
              >
                {t('Set up')}
              </Button>
            }
          />
        );
    }
  };

  const isActive = !!client && status?.state === 'active';

  return (
    <section className="account-panel encryption-panel">
      <header className="account-panel__header encryption-panel__header">
        <h1>{t('Encryption')}</h1>
        <p>{t('Manage your account encryption settings.')}</p>
      </header>

      {renderBanner()}

      {isActive && (
        <>
          <div className="account-panel__section">
            <h2>{t('Your encryption settings')}</h2>
            <ul className="encryption-settings">
              <SettingRow
                title={t('Set up another device')}
                description={t(
                  'Use this device to give another device access to your encrypted documents.',
                )}
                action={
                  <Button
                    size="nano"
                    color="brand"
                    variant="bordered"
                    icon={<PhoneDesktop size={16} />}
                    onClick={() => openSettings('add-device')}
                  >
                    {t('Add a device')}
                  </Button>
                }
              />
              <SettingRow
                title={t('Verification code')}
                description={t(
                  'Let others verify your identity by comparing this code.',
                )}
                action={
                  <Button
                    size="nano"
                    color="brand"
                    variant="bordered"
                    icon={<Eye size={16} />}
                    onClick={() => openSettings('verification-code')}
                  >
                    {t('Show code')}
                  </Button>
                }
              />
            </ul>
          </div>

          <div className="account-panel__section">
            <h2>{t('Recovery')}</h2>
            <ul className="encryption-settings">
              <SettingRow
                title={t('Recovery phrase')}
                description={t(
                  "Your recovery phrase lets you access your encrypted documents when you can't use another device.",
                )}
                action={
                  <Button
                    size="nano"
                    color="neutral"
                    variant="bordered"
                    onClick={() => openSettings('recovery-phrase')}
                  >
                    {t('Change recovery phrase')}
                  </Button>
                }
              />
              <SettingRow
                title={t('Trusted contacts')}
                description={t(
                  'Choose who can help you recover access to your encrypted documents, and see who you can help.',
                )}
                action={
                  <Button
                    size="nano"
                    color="neutral"
                    variant="bordered"
                    onClick={() => openSettings('trusted-contacts')}
                  >
                    {t('Manage trusted contacts')}
                  </Button>
                }
              />
            </ul>
          </div>
        </>
      )}

      {flow && (
        <EncryptionInterfaceModal
          key={flowId}
          flow={flow}
          onClose={closeFlow}
        />
      )}
    </section>
  );
};
