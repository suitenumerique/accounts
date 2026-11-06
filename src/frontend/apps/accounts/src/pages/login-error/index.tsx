import Head from 'next/head';
import { useRouter } from 'next/router';
import { Button } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

import { AppHeaderLayout } from '@/components/Layout/AppHeaderLayout';

export default function LoginErrorPage() {
  const { t } = useTranslation();
  const router = useRouter();

  return (
    <div className="login-error-page">
      <Head>
        <title>{t('Sign-in failed')} | La Suite</title>
      </Head>
      <AppHeaderLayout>
        <div className="login-error-page__canvas">
          <div className="login-error-page__content">
            <div className="login-error-page__illustration" aria-hidden="true">
              <img
                className="login-error-page__illustration-image"
                src="/assets/union.svg"
                alt=""
                width="160"
                height="160"
              />
            </div>

            <h1>{t('Sign-in failed')}</h1>
            <p>
              {t(
                'A technical issue is preventing sign-in right now. Please try again in a few moments.',
              )}
            </p>

            <div className="login-error-page__actions">
              <Button fullWidth onClick={() => void router.push('/login/')}>
                {t('Try again')}
              </Button>
            </div>
          </div>
        </div>
      </AppHeaderLayout>
    </div>
  );
}
