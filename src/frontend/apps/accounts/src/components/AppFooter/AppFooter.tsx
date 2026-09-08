'use client';

import dynamic from 'next/dynamic';

import { AppHelpMenu } from '@/components/AppHelpMenu/AppHelpMenu';

const LaGaufre = dynamic(
  () => import('@gouvfr-lasuite/ui-kit').then((module) => module.LaGaufreV2),
  { ssr: false },
);

export const AppFooter = () => (
  <footer className="suite__footer">
    <div className="suite__footer__gaufre">
      <LaGaufre apiUrl="https://lasuite.numerique.gouv.fr/api/services"
      widgetPath="https://static.suite.anct.gouv.fr/widgets/lagaufre.js" />
    </div>
    <div className="suite__footer__help">
      <AppHelpMenu />
    </div>
  </footer>
);
