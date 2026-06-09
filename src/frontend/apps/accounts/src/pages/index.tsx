import { Button } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

import { login, useAuth } from '@/features/auth/Auth';

export default function HomePage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  if (user) {
    return (
      <main className="welcome">
        <div>
          <h1>{t('Welcome on LaSuite Account')} </h1>
          <Button disabled>{t('Logout')}</Button>
        </div>
      </main>
    );
  }

  return (
    <main className="login-home">
      <Button onClick={() => login()}>{t('Login')}</Button>
    </main>
  );
}
