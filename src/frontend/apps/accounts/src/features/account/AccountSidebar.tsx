'use client';

import dynamic from 'next/dynamic';
import { useTranslation } from 'react-i18next';

import { User } from '@/features/auth/types';

import {
  PersonalInformationIcon,
  SecurityIcon,
} from './AccountNavIcons';

const UserAvatar = dynamic(
  () => import('@gouvfr-lasuite/ui-kit').then((module) => module.UserAvatar),
  { ssr: false },
);

export type AccountSection = 'personal' | 'security';

type AccountSidebarProps = {
  user: User;
  activeSection: AccountSection;
  onSelectSection: (section: AccountSection) => void;
};

export const AccountSidebar = ({
  user,
  activeSection,
  onSelectSection,
}: AccountSidebarProps) => {
  const { t } = useTranslation();
  const displayName = user.full_name || user.email;

  return (
    <aside className="account-sidebar">
      <div className="account-sidebar__profile">
        <UserAvatar fullName={displayName} size="large" />
        <div className="account-sidebar__profile-text">
          <p className="account-sidebar__title">{t('My account')}</p>
          <p className="account-sidebar__name">{displayName}</p>
        </div>
      </div>

      <nav className="account-sidebar__nav" aria-label={t('My account')}>
        <button
          type="button"
          className={[
            'account-sidebar__nav-item',
            activeSection === 'personal' && 'account-sidebar__nav-item--active',
          ]
            .filter(Boolean)
            .join(' ')}
          onClick={() => onSelectSection('personal')}
          aria-current={activeSection === 'personal' ? 'page' : undefined}
        >
          <PersonalInformationIcon />
          <span>{t('Personal information')}</span>
        </button>

        <button
          type="button"
          className={[
            'account-sidebar__nav-item',
            activeSection === 'security' && 'account-sidebar__nav-item--active',
          ]
            .filter(Boolean)
            .join(' ')}
          onClick={() => onSelectSection('security')}
          aria-current={activeSection === 'security' ? 'page' : undefined}
        >
          <SecurityIcon />
          <span>{t('Security and sign-in')}</span>
        </button>
      </nav>
    </aside>
  );
};
