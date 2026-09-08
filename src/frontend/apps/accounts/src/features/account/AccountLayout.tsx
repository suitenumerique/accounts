'use client';

import { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';

import { AppFooter } from '@/components/AppFooter/AppFooter';
import { AppHeaderLayout } from '@/components/Layout/AppHeaderLayout';
import { LaSuiteLogo } from '@/components/Logo/LaSuiteLogo';

type AccountLayoutProps = {
  sidebar: ReactNode;
  children: ReactNode;
  showSidebar?: boolean;
  isMobile?: boolean;
  onBack?: () => void;
  showBack?: boolean;
};

export const AccountLayout = ({
  sidebar,
  children,
  showSidebar = true,
  isMobile = false,
  onBack,
  showBack = false,
}: AccountLayoutProps) => {
  const { t } = useTranslation();

  const body = (
    <div
      className={[
        'account-layout',
        showSidebar
          ? 'account-layout--sidebar'
          : 'account-layout--content',
      ].join(' ')}
    >
      <aside className="account-layout__sidebar">{sidebar}</aside>
      <main className="account-layout__main">{children}</main>
    </div>
  );

  if (!isMobile) {
    return (
      <AppHeaderLayout
        className="account-page__layout"
        hideLeftPanelOnDesktop
        logo={<LaSuiteLogo variant="wordmark" />}
      >
        {body}
      </AppHeaderLayout>
    );
  }

  return (
    <div className="account-shell">
      <header className="account-header">
        <div className="account-header__inner">
          {showBack ? (
            <button
              type="button"
              className="account-header__back"
              onClick={onBack}
              aria-label={t('Back')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M11.293 4.29289C11.6835 3.90237 12.3165 3.90237 12.707 4.29289C13.0976 4.68342 13.0976 5.31643 12.707 5.70696L7.41406 10.9999H19C19.5523 10.9999 20 11.4476 20 11.9999C20 12.5522 19.5523 12.9999 19 12.9999H7.41406L12.707 18.2929C13.0976 18.6834 13.0976 19.3164 12.707 19.707C12.3165 20.0975 11.6835 20.0975 11.293 19.707L4.29297 12.707C3.90245 12.3164 3.90245 11.6834 4.29297 11.2929L11.293 4.29289Z" fill="#626A80"/>
              </svg>
            </button>
          ) : (
            <span className="account-header__spacer" aria-hidden="true" />
          )}
          <LaSuiteLogo variant="mark" className="account-header__logo" />
          <span className="account-header__spacer" aria-hidden="true" />
        </div>
      </header>

      {body}

      <AppFooter />
    </div>
  );
};
