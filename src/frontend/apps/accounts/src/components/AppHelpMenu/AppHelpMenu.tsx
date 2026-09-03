'use client';

import { HelpMenu } from '@gouvfr-lasuite/ui-kit';

import './AppHelpMenu.scss';

const DOCUMENTATION_URL = '';
const CONTACT_EMAIL = '';

export const AppHelpMenu = () => (
  <div className="app-help-menu">
    <HelpMenu
      documentationUrl={DOCUMENTATION_URL}
      onContactUs={() => {
        window.location.href = `mailto:${CONTACT_EMAIL}`;
      }}
    />
  </div>
);
