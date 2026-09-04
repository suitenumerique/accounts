import { FormEvent, useState } from 'react';
import Head from 'next/head';
import { Button } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

import { AppHeaderLayout } from '@/components/layout/AppHeaderLayout';
import { login } from '@/features/auth/Auth';

export default function LoginPage() {
  const { t } = useTranslation();
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    login(email.trim());
  };

  return (
    <div className="login-page">
      <Head>
        <title>{t('Sign in to LaSuite')}</title>
      </Head>
      <AppHeaderLayout>
        <div className="login-page__canvas">
          <form
            className="login-page__form"
            onSubmit={handleSubmit}
            aria-busy={isSubmitting}
          >
            <div className="login-page__illustration" aria-hidden="true">
              <img
                className="login-page__illustration-image"
                src="/assets/union.svg"
                alt=""
                width="160"
                height="160"
              />
            </div>

            <h1>{t('Sign in to LaSuite')}</h1>

            <div className="login-page__field">
              <label className="login-page__label" htmlFor="login-email">
                {t('Email address')}
              </label>
              <input
                id="login-email"
                className="login-page__input"
                type="email"
                name="email"
                autoComplete="email"
                placeholder={t('Email address')}
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                disabled={isSubmitting}
              />
              <p className="login-page__hint">
                {t('Type your ProConnect address to continue.')}
              </p>
            </div>

            <div className="login-page__actions">
              <Button type="submit" fullWidth disabled={!email.trim() || isSubmitting}>
                {t('Sign in')}
              </Button>
            </div>
          </form>
        </div>
      </AppHeaderLayout>
    </div>
  );
}
