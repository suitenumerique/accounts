'use client';

import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { useTranslation } from 'react-i18next';

import { useAuth } from '@/features/auth/Auth';
import { useLocales } from '@/i18n/useLocale';

const UserMenu = dynamic(
  () => import('@gouvfr-lasuite/ui-kit').then((module) => module.UserMenu),
  { ssr: false },
);

const LanguagePicker = dynamic(
  () =>
    import('@gouvfr-lasuite/ui-kit').then((module) => module.LanguagePicker),
  { ssr: false },
);

// const TERM_OF_SERVICE_URL =
//   'https://docs.numerique.gouv.fr/docs/8e298e03-c95f-44c7-be4a-ffb618af1854/';

const LANGUAGES = [
  { label: 'Français', shortLabel: 'FR', value: 'fr-FR' },
  { label: 'English', shortLabel: 'EN', value: 'en-US' },
  { label: 'Deutsch', shortLabel: 'DE', value: 'de-DE' },
] as const;

export const AppUserMenu = () => {
  const { user } = useAuth();
  const router = useRouter();
  const { i18n } = useTranslation();
  const currentLocale = useLocales();

  if (!user) {
    return null;
  }

  return (
    <div className="app-user-menu">
      <UserMenu
        user={{
          email: user.email,
          full_name: user.full_name || undefined,
        }}
        logout={() => {
          void router.push('/logout');
        }}
        // termOfServiceUrl={TERM_OF_SERVICE_URL}
        withMobileView={false}
        actions={
          <LanguagePicker
            compact
            size="small"
            languages={LANGUAGES.map((language) => ({
              ...language,
              isChecked: language.value === currentLocale,
            }))}
            onChange={(nextLanguage) => {
              void i18n.changeLanguage(nextLanguage.slice(0, 2).toLowerCase());
            }}
          />
        }
      />
    </div>
  );
};
