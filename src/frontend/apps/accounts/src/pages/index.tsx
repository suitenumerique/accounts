import { Button } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

import { login, useAuth } from '@/features/auth/Auth';
import {LOGOUT_URL} from "@/features/auth/conf";
import {getCSRFToken} from "@/features/api/fetchApi";

export default function HomePage() {
  const { t } = useTranslation();
  const { user } = useAuth();

  if (user) {
    return (
      <main className="welcome">
        <div>
          <h1>{t('Welcome on LaSuite Account')} </h1>
          <form action={LOGOUT_URL} method="post">
            <input type="hidden" name="csrfmiddlewaretoken" value={getCSRFToken()}/>
            <Button>{t('Logout')}</Button>
          </form>
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
