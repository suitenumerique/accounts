'use client';

import { HelpMenu } from '@gouvfr-lasuite/ui-kit';

const CONTACT_EMAIL = 'support-lasuite@numerique.gouv.fr';

export const AppHelpMenu = () => (
  <div className="app-help-menu">
    <HelpMenu
      onContactUs={() => {
        window.location.href = `mailto:${CONTACT_EMAIL}`;
      }}
    />
  </div>
);
