'use client';

import dynamic from 'next/dynamic';

import {
  AppFeedbackButton,
  useFeedbackFormUrl,
} from '@/components/AppFeedbackButton/AppFeedbackButton';
import { AppHelpMenu } from '@/components/AppHelpMenu/AppHelpMenu';
import { AppUserMenu } from '@/components/AppUserMenu/AppUserMenu';

const LaGaufre = dynamic(
  () => import('@gouvfr-lasuite/ui-kit').then((module) => module.LaGaufreV2),
  { ssr: false },
);

export const AppFooter = () => {
  const feedbackFormUrl = useFeedbackFormUrl();

  return (
    <footer className="suite__footer">
      <div className="suite__footer__user">
        <AppUserMenu />
      </div>
      <div className="suite__footer__gaufre">
        <LaGaufre
          apiUrl="https://lasuite.numerique.gouv.fr/api/services"
          widgetPath="https://static.suite.anct.gouv.fr/widgets/lagaufre.js"
        />
      </div>
      {feedbackFormUrl ? (
        <AppFeedbackButton url={feedbackFormUrl} />
      ) : (
        <div className="suite__footer__help">
          <AppHelpMenu />
        </div>
      )}
    </footer>
  );
};
