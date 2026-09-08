import AccountPage from '@/features/account/AccountPage';
import { useAuth } from '@/features/auth/Auth';

import LoginPage from './login/LoginPage';

export default function HomePage() {
  const { user } = useAuth();

  if (user) {
    return <AccountPage user={user} />;
  }

  return <LoginPage />;
}
