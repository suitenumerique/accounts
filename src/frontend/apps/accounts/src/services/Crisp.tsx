/**
 * Configure Crisp chat for real-time support across all pages.
 */

import { ChatboxPosition, Crisp } from 'crisp-sdk-web';
import { JSX, PropsWithChildren, ReactNode, useEffect, useState } from 'react';
import { createGlobalStyle } from 'styled-components';

import { User } from '@/features/auth';
import { AbstractAnalytic, AnalyticEvent } from '@/libs';

const CrispStyle = createGlobalStyle`
  #crisp-chatbox div[role="button"] {
    zoom: 0.7;
    right: auto !important;
    left: 24px !important;
  }

  #crisp-chatbox div[data-chat-status="initial"] {
    bottom: 65px!important;
    left: 24px !important;
    margin-left: var(--crisp-customization-button-horizontal) !important;
    right: auto !important;
  }
`;

export const initializeCrispSession = (user: User) => {
  if (!Crisp.isCrispInjected()) {
    return;
  }
  Crisp.setTokenId(`accounts-${user.id}`);
  Crisp.user.setEmail(user.email);
};

export const configureCrispSession = (websiteId: string) => {
  if (Crisp.isCrispInjected()) {
    return;
  }
  Crisp.configure(websiteId);
  Crisp.setSafeMode(true);
  Crisp.setPosition(ChatboxPosition.Left);
  Crisp.chat.hide();
  Crisp.chat.onChatClosed(() => {
    Crisp.chat.hide();
  });
};

export const openCrispChat = () => {
  if (!Crisp.isCrispInjected()) {
    return;
  }
  Crisp.setPosition(ChatboxPosition.Left);
  Crisp.chat.show();
  setTimeout(() => {
    Crisp.chat.open();
  }, 300);
};

export const terminateCrispSession = () => {
  if (!Crisp.isCrispInjected()) {
    return;
  }
  Crisp.setTokenId();
  Crisp.session.reset();
};

interface CrispProviderProps {
  websiteId?: string;
}

export const CrispProvider = ({
  children,
  websiteId,
}: PropsWithChildren<CrispProviderProps>) => {
  const [isConfigured, setIsConfigured] = useState(false);

  useEffect(() => {
    if (!websiteId) {
      return;
    }

    setIsConfigured(true);
    configureCrispSession(websiteId);
  }, [websiteId]);

  return (
    <>
      {isConfigured && <CrispStyle />}
      {children}
    </>
  );
};

export class CrispAnalytic extends AbstractAnalytic {
  private conf?: CrispProviderProps = undefined;
  private EVENT = {
    PUBLIC_DOC_NOT_CONNECTED: 'public-doc-not-connected',
  };

  public constructor(conf?: CrispProviderProps) {
    super();

    this.conf = conf;
  }

  public Provider(children?: ReactNode): JSX.Element {
    return (
      <CrispProvider websiteId={this.conf?.websiteId}>{children}</CrispProvider>
    );
  }

  public trackEvent(evt: AnalyticEvent): void {
    if (evt.eventName === 'doc') {
      if (evt.isPublic && !evt.authenticated) {
        Crisp.trigger.run(this.EVENT.PUBLIC_DOC_NOT_CONNECTED);
      }
    }
  }

  public isFeatureFlagActivated(): boolean {
    return true;
  }
}
