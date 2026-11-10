'use client';

import { HelpMenu } from '@gouvfr-lasuite/ui-kit';

import { useAuth } from '@/features/auth/Auth';
import {
  SUPPORT_API_BASE,
  SUPPORT_CHANNEL,
  SUPPORT_SCRIPT_SRC,
} from '@/features/support/constants';
import { openSupportWidget } from '@/features/support/openSupportWidget';

export const AppHelpMenu = () => {
  const { user } = useAuth();

  return (
    <div className="app-help-menu">
      <HelpMenu
        onContactUs={() => {
          openSupportWidget({
            scriptSrc: SUPPORT_SCRIPT_SRC,
            apiBase: SUPPORT_API_BASE,
            channel: SUPPORT_CHANNEL,
            email: user?.email,
            position: 'bottom-left',
          });
        }}
      />
    </div>
  );
};
