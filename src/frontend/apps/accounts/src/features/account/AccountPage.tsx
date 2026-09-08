'use client';

import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useTranslation } from 'react-i18next';

import { User } from '@/features/auth/types';

import { AccountLayout } from './AccountLayout';
import {
  AccountSection,
  AccountSidebar,
} from './AccountSidebar';
import { PersonalInformationPanel } from './PersonalInformationPanel';
import { SecurityPanel } from './SecurityPanel';

type AccountPageProps = {
  user: User;
};

const MOBILE_BREAKPOINT = 1024;

export default function AccountPage({ user }: AccountPageProps) {
  const { t } = useTranslation();
  const [activeSection, setActiveSection] =
    useState<AccountSection>('personal');
  const [isMobile, setIsMobile] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(true);

  useEffect(() => {
    const mediaQuery = window.matchMedia(
      `(max-width: ${MOBILE_BREAKPOINT - 1}px)`,
    );

    const syncViewport = () => {
      const nextIsMobile = mediaQuery.matches;
      setIsMobile(nextIsMobile);
      setShowMobileMenu(nextIsMobile);
    };

    syncViewport();
    mediaQuery.addEventListener('change', syncViewport);

    return () => {
      mediaQuery.removeEventListener('change', syncViewport);
    };
  }, []);

  const handleSelectSection = (section: AccountSection) => {
    setActiveSection(section);
    if (isMobile) {
      setShowMobileMenu(false);
    }
  };

  const showSidebar = !isMobile || showMobileMenu;
  const showBack = isMobile && !showMobileMenu;

  return (
    <div className="account-page">
      <Head>
        <title>{t('My account')}</title>
      </Head>
      <AccountLayout
        sidebar={
          <AccountSidebar
            user={user}
            activeSection={activeSection}
            onSelectSection={handleSelectSection}
          />
        }
        showSidebar={showSidebar}
        isMobile={isMobile}
        showBack={showBack}
        onBack={() => setShowMobileMenu(true)}
      >
        <div className="account-page__content">
          {activeSection === 'personal' ? (
            <PersonalInformationPanel user={user} />
          ) : (
            <SecurityPanel />
          )}
        </div>
      </AccountLayout>
    </div>
  );
}
