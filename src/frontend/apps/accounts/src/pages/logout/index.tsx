import { FormEvent, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { Button } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

import { AppHeaderLayout } from '@/components/layout/AppHeaderLayout';
import { getCSRFToken } from '@/features/api/fetchApi';
import { OIDC_LOGOUT_URL } from '@/features/auth/conf';

const LOGOUT_QUERY_PARAMETERS = [
  'id_token_hint',
  'client_id',
  'post_logout_redirect_uri',
  'state',
] as const;

const getQueryValue = (value: string | string[] | undefined) => {
  if (Array.isArray(value)) {
    return value.at(-1);
  }

  return value;
};

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
      <AppHeaderLayout>
        <div className="logout-page__canvas">
          <form
            className="logout-page__form"
            action={OIDC_LOGOUT_URL}
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
            <input type="hidden" name="allow" value="true" />

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
      </AppHeaderLayout>
    </div>
  );
}

LogoutPage.isStandalonePage = true;
