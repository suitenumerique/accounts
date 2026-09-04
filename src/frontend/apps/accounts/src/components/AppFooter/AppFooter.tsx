'use client';

import dynamic from 'next/dynamic';

import { AppHelpMenu } from '@/components/AppHelpMenu/AppHelpMenu';

import './AppFooter.scss';

const LaGaufre = dynamic(
  () => import('@gouvfr-lasuite/ui-kit').then((module) => module.LaGaufre),
  { ssr: false },
);

export const AppFooter = () => (
  <footer className="suite__footer">
    <div className="suite__footer__gaufre">
      <LaGaufre />
    </div>
    <div className="suite__footer__help">
      <AppHelpMenu />
    </div>
  </footer>
);
