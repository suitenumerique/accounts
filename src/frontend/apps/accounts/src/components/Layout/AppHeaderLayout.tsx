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
  logo?: ReactNode;
};

export const AppHeaderLayout = ({
  children,
  className,
  hideLeftPanelOnDesktop = true,
  logo = <LaSuiteLogo />,
}: AppHeaderLayoutProps) => (
  <div
    className={['app-header-layout', className].filter(Boolean).join(' ')}
  >
    <MainLayout icon={logo} hideLeftPanelOnDesktop={hideLeftPanelOnDesktop}>
      {children}
    </MainLayout>
    <AppFooter />
  </div>
);
