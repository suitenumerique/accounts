import { ReactNode } from 'react';
import dynamic from 'next/dynamic';

import { LaSuiteLogo } from '@/components/Logo/LaSuiteLogo';
import { AppFooter } from '@/components/AppFooter/AppFooter';
import type { ProductId } from '@/features/product/products';
import { useProduct } from '@/features/product/useProduct';

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
  product?: ProductId | string | null;
  showMenuToggle?: boolean;
  isLeftPanelOpen?: boolean;
  setIsLeftPanelOpen?: (isLeftPanelOpen: boolean) => void;
};

export const AppHeaderLayout = ({
  children,
  className = '',
  hideLeftPanelOnDesktop = true,
  leftPanelContent,
  logo,
  product,
  showMenuToggle = false,
  isLeftPanelOpen,
  setIsLeftPanelOpen,
}: AppHeaderLayoutProps) => {
  const { productId } = useProduct(product);

  return (
    <div
      className={`app-header-layout${showMenuToggle ? ' app-header-layout--with-menu-toggle' : ''} ${className}`.trim()}
    >
      <MainLayout
        icon={logo ?? <LaSuiteLogo product={productId} />}
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
};
