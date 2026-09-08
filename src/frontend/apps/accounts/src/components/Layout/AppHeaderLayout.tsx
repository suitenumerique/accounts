import { ReactNode } from 'react';
import dynamic from 'next/dynamic';

import { LaSuiteLogo } from '@/components/Logo/LaSuiteLogo';
import { AppFooter } from '@/components/AppFooter/AppFooter';

const MainLayout = dynamic(
  () => import('@gouvfr-lasuite/ui-kit').then((module) => module.MainLayout),
  { ssr: false },
);

type AppHeaderLayoutProps = {
  children: ReactNode;
  className?: string;
  hideLeftPanelOnDesktop?: boolean;
  leftPanelContent?: ReactNode;
  logo?: ReactNode;
  showMenuToggle?: boolean;
  isLeftPanelOpen?: boolean;
  setIsLeftPanelOpen?: (isLeftPanelOpen: boolean) => void;
};

export const AppHeaderLayout = ({
  children,
  className,
  hideLeftPanelOnDesktop = true,
  leftPanelContent,
  logo = <LaSuiteLogo />,
  showMenuToggle = false,
  isLeftPanelOpen,
  setIsLeftPanelOpen,
}: AppHeaderLayoutProps) => (
  <div
    className={[
      'app-header-layout',
      showMenuToggle && 'app-header-layout--with-menu-toggle',
      className,
    ]
      .filter(Boolean)
      .join(' ')}
  >
    <MainLayout
      icon={logo}
      hideLeftPanelOnDesktop={hideLeftPanelOnDesktop}
      leftPanelContent={leftPanelContent}
      isLeftPanelOpen={isLeftPanelOpen}
      setIsLeftPanelOpen={setIsLeftPanelOpen}
    >
      {children}
    </MainLayout>
    <AppFooter />
  </div>
);
