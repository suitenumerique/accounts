'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { Input } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

import { useAuth } from '@/features/auth/Auth';
import { User } from '@/features/auth/types';
import { useConfig } from '@/features/config/ConfigProvider';

// const LanguagePicker = dynamic(
//   () =>
//     import('@gouvfr-lasuite/ui-kit').then((module) => module.LanguagePicker),
//   { ssr: false },
// );

const PROCONNECT_URL = 'https://www.proconnect.gouv.fr/';

type PersonalInformationPanelProps = {
  user: User;
};

export const PersonalInformationPanel = ({
  user,
}: PersonalInformationPanelProps) => {
  const { t } = useTranslation();
  const { config } = useConfig();
  // const [language] = useState(user.language || config.LANGUAGE_CODE);
  // const [isSavingLanguage, setIsSavingLanguage] = useState(false);

  return (
    <section className="account-panel">
      <header className="account-panel__header">
        <h1>{t('Personal information')}</h1>
        <p>
          {t('View your personal information. Your name and email address are managed by')}{' '}
          <a
            className="account-panel__external-link"
            href={PROCONNECT_URL}
            target="_blank"
            rel="noreferrer"
          >
            ProConnect
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="12"
              height="12"
              viewBox="0 0 12 12"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M4.5 2.5H2.5C1.94772 2.5 1.5 2.94772 1.5 3.5V9.5C1.5 10.0523 1.94772 10.5 2.5 10.5H8.5C9.05228 10.5 9.5 10.0523 9.5 9.5V7.5M7 1.5H10.5M10.5 1.5V5M10.5 1.5L5 7"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </a>
          .
        </p>
      </header>

      <div className="account-panel__section">
        <h2>{t('Identity')}</h2>
        <div className="account-panel__fields">
          <Input
            label={t('Name')}
            variant="classic"
            value={user.full_name || ''}
            fullWidth
            disabled
            text={t('Managed by ProConnect')}
          />
          <Input
            label={t('Email')}
            variant="classic"
            value={user.email}
            fullWidth
            disabled
            text={t('Managed by ProConnect')}
          />
        </div>
      </div>
{/*
      <div className="account-panel__section">
        <h2>{t('Language')}</h2>
        <div className="account-panel__language">
          <div className="account-panel__language-copy">
            <p className="account-panel__language-label">{t('Display language')}</p>
            <p className="account-panel__language-hint">
              {t('Choose the language used on this page.')}
            </p>
          </div>
          <LanguagePicker
            languages={languageOptions}
            onChange={(nextLanguage) => {
              void handleLanguageChange(nextLanguage);
            }}
            compact
            size="small"
            variant="tertiary"
          />
        </div>
      </div>*/}
    </section>
  );
};
