'use client';

import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useTranslation } from 'react-i18next';

import { User } from '@/features/auth/types';
import { EncryptionPanel } from '@/features/encryption/EncryptionPanel';
import { useVaultClient } from '@/features/encryption/VaultClientProvider';

import { AccountLayout } from './AccountLayout';
import { AccountSection, AccountSidebar } from './AccountSidebar';
import { PersonalInformationPanel } from './PersonalInformationPanel';
import { SecurityPanel } from './SecurityPanel';

type AccountPageProps = {
  user: User;
};

const MOBILE_BREAKPOINT = 1024;

const ACCOUNT_SECTIONS: AccountSection[] = [
  'personal',
  'security',
  'encryption',
];

const isAccountSection = (value: unknown): value is AccountSection =>
  typeof value === 'string' &&
  ACCOUNT_SECTIONS.includes(value as AccountSection);

export default function AccountPage({ user }: AccountPageProps) {
  const { t } = useTranslation();
  const { isEnabled: isEncryptionEnabled } = useVaultClient();
  const [activeSection, setActiveSection] =
    useState<AccountSection>('personal');
  const [isMobile, setIsMobile] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(true);
  const router = useRouter();
  const requestedSection = router.isReady ? router.query.section : undefined;

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

  // A product links straight to one section (`/?section=encryption` from the
  // products' encryption menu). The encryption section exists only once the
  // feature is known to be enabled, so the link waits for the configuration.
  // Applied while rendering, once per requested section.
  const [appliedSection, setAppliedSection] = useState<AccountSection | null>(
    null,
  );
  const linkedSection =
    isAccountSection(requestedSection) &&
    (requestedSection !== 'encryption' || isEncryptionEnabled)
      ? requestedSection
      : null;

  if (linkedSection && linkedSection !== appliedSection) {
    setAppliedSection(linkedSection);
    setActiveSection(linkedSection);
    setShowMobileMenu(false);
  }

  const handleSelectSection = (section: AccountSection) => {
    setActiveSection(section);
    if (isMobile) {
      setShowMobileMenu(false);
    }
    // Keep the address shareable and a reload on the same section.
    void router.replace({ query: { ...router.query, section } }, undefined, {
      shallow: true,
    });
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
          {activeSection === 'personal' && (
            <PersonalInformationPanel user={user} />
          )}
          {activeSection === 'security' && <SecurityPanel />}
          {activeSection === 'encryption' && isEncryptionEnabled && (
            <EncryptionPanel />
          )}
        </div>
      </AccountLayout>
    </div>
  );
}
