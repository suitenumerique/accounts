import { FormEvent, useState } from 'react';
import dynamic from 'next/dynamic';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Button } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

import { getCSRFToken } from '@/features/api/fetchApi';
import { LOGOUT_URL } from '@/features/auth/conf';

const MainLayout = dynamic(
  () => import('@gouvfr-lasuite/ui-kit').then((module) => module.MainLayout),
  { ssr: false },
);

const LOGOUT_QUERY_PARAMETERS = [
  'state',
] as const;

const getQueryValue = (value: string | string[] | undefined) => {
  if (Array.isArray(value)) {
    return value.at(-1);
  }

  return value;
};

const LaSuiteLogo = () => (
  <span className="logout-page__logo" role="img" aria-label="La Suite">
    <img
      className="logout-page__logo-wordmark"
      src="/assets/lasuite-logo-wordmark.svg"
      alt=""
      width="88"
      height="27"
    />
    <img
      className="logout-page__logo-mark"
      src="/assets/lasuite-logo-mark.svg"
      alt=""
      width="15"
      height="17"
    />
  </span>
);

export default function LogoutPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const csrfToken =
    typeof document === 'undefined' ? '' : (getCSRFToken() ?? '');

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    if (!router.isReady || !csrfToken) {
      event.preventDefault();
      return;
    }

    setIsSubmitting(true);
  };

  return (
    <div className="logout-page">
      <Head>
        <title>{t('Do you want to sign out?')} | La Suite</title>
      </Head>
      <MainLayout icon={<LaSuiteLogo />} hideLeftPanelOnDesktop>
        <div className="logout-page__canvas">
          <form
            className="logout-page__form"
            action={LOGOUT_URL}
            method="post"
            onSubmit={handleSubmit}
            aria-busy={isSubmitting}
          >
            <div className="logout-page__illustration" aria-hidden="true">
              <img
                className="logout-page__illustration-pattern"
                src="/assets/logout-illustration.svg"
                alt=""
                width="160"
                height="160"
              />
              <img
                className="logout-page__illustration-icon"
                src="/assets/logout-exit-icon.svg"
                alt=""
                width="34"
                height="34"
              />
            </div>

            <h1>{t('Do you want to sign out?')}</h1>

            <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken} />
            {router.isReady &&
              LOGOUT_QUERY_PARAMETERS.map((parameter) => {
                const value = getQueryValue(router.query[parameter]);

                return value === undefined ? null : (
                  <input
                    key={parameter}
                    type="hidden"
                    name={parameter}
                    value={value}
                  />
                );
              })}

            <div className="logout-page__actions">
              <Button
                type="submit"
                fullWidth
                disabled={!router.isReady || !csrfToken || isSubmitting}
              >
                {t('Confirm sign out')}
              </Button>
              <Button
                type="button"
                fullWidth
                color="neutral"
                variant="tertiary"
                onClick={() => window.history.back()}
              >
                {t('Cancel')}
              </Button>
            </div>
          </form>
        </div>
      </MainLayout>
    </div>
  );
}

LogoutPage.isStandalonePage = true;
