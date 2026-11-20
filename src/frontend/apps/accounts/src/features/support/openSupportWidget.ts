const WIDGET_NAME = 'support';
const WIDGET_SCRIPT_ID = 'lasuite-support-widget';

declare global {
  interface Window {
    _lasuite_widget?: unknown[];
  }
}

export type SupportWidgetPosition =
  | 'bottom-left'
  | 'bottom-right'
  | 'top-right';

export type OpenSupportWidgetOptions = {
  apiBase: string;
  channel: string;
  scriptSrc: string;
  email?: string;
  position?: SupportWidgetPosition;
};

const ensureTrailingSlash = (url: string) =>
  url.endsWith('/') ? url : `${url}/`;

const ensureScript = (scriptSrc: string) => {
  if (document.getElementById(WIDGET_SCRIPT_ID)) {
    return;
  }

  const script = document.createElement('script');
  script.id = WIDGET_SCRIPT_ID;
  script.src = scriptSrc;
  script.async = true;
  document.body.appendChild(script);
};

const getSupportPanel = (): HTMLElement | null => {
  const host = document.getElementById('lasuite-widget-support-root');
  const inShadow = host?.shadowRoot?.querySelector(
    '[role="dialog"]',
  ) as HTMLElement | null;
  if (inShadow) {
    return inShadow;
  }
  // Older bundles mounted React in light DOM.
  const inLight = document.querySelector(
    '#lasuite-widget-support-root [role="dialog"]',
  ) as HTMLElement | null;
  if (inLight) {
    return inLight;
  }
  return document
    .getElementById('lasuite-widget-support-shadow')
    ?.shadowRoot?.querySelector('#wrapper') as HTMLElement | null;
};

const forcePosition = (position: SupportWidgetPosition) => {
  const panel = getSupportPanel();
  if (!panel) {
    return;
  }

  panel.style.inset = 'auto';
  panel.style.width = 'min(400px, calc(100vw - 24px))';
  panel.style.maxHeight = 'calc(100vh - 40px)';

  if (position === 'top-right') {
    panel.style.top = '80px';
    panel.style.right = '20px';
    panel.style.bottom = 'auto';
    panel.style.left = 'auto';
    return;
  }

  panel.style.top = 'auto';
  panel.style.bottom = '20px';
  if (position === 'bottom-left') {
    panel.style.left = '20px';
    panel.style.right = 'auto';
  } else {
    panel.style.right = '20px';
    panel.style.left = 'auto';
  }
};

/**
 * Opens the shared La Suite support widget.
 * Queues `init` on `_lasuite_widget` so it works whether the script
 * is already loaded or still downloading.
 */
export const openSupportWidget = ({
  apiBase,
  channel,
  scriptSrc,
  email,
  position = 'bottom-right',
}: OpenSupportWidgetOptions) => {
  const onOpened = () => {
    // Ensure placement even if an older support.js ignores `position`.
    requestAnimationFrame(() => forcePosition(position));
    document.removeEventListener('lasuite-widget-support-opened', onOpened);
  };
  document.addEventListener('lasuite-widget-support-opened', onOpened);

  window._lasuite_widget = window._lasuite_widget || [];
  window._lasuite_widget.push([
    WIDGET_NAME,
    'init',
    {
      api: ensureTrailingSlash(apiBase),
      channel,
      position,
      ...(email ? { email } : {}),
    },
  ]);
  ensureScript(scriptSrc);
};
