'use client';

import { Button } from '@gouvfr-lasuite/cunningham-react';
import { useTranslation } from 'react-i18next';

const PROCONNECT_URL = 'https://www.proconnect.gouv.fr/';

const ExternalLinkIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
    <path d="M17 6C17.0563 6 17.1113 6.00571 17.165 6.01465C17.1751 6.01633 17.1853 6.01754 17.1953 6.01953C17.2105 6.02254 17.2253 6.02659 17.2402 6.03027C17.2562 6.0342 17.2723 6.03727 17.2881 6.04199C17.3382 6.05705 17.3861 6.07723 17.4326 6.09961C17.4466 6.10634 17.4609 6.11269 17.4746 6.12012C17.6203 6.19887 17.7441 6.31255 17.835 6.4502C17.8597 6.48768 17.8812 6.52662 17.9004 6.56641C17.9637 6.69767 18 6.8445 18 7V17C18 17.5523 17.5523 18 17 18C16.4477 18 16 17.5523 16 17V9.41406L7.70703 17.707C7.31651 18.0976 6.68349 18.0976 6.29297 17.707C5.90246 17.3165 5.90245 16.6835 6.29297 16.293L14.5859 8H7C6.44772 8 6 7.55228 6 7C6 6.44772 6.44772 6 7 6H17Z" fill="#626A80"/>
  </svg>
);

export const SecurityPanel = () => {
  const { t } = useTranslation();

  return (
    <section className="account-panel">
      <header className="account-panel__header">
        <h1>{t('Security and sign-in')}</h1>
        <p>{t('Manage how you sign in and protect your account.')}</p>
      </header>

      <div className="account-panel__section">
        <h2>{t('Sign-in provider')}</h2>
        <div className="security-provider">
          <div className="security-provider__brand">
            <img
              className="security-provider__logo"
              src="/assets/proconnect-logo.svg"
              alt=""
              width="auto"
              height="32"
            />
          </div>
          <Button
            href={PROCONNECT_URL}
            target="_blank"
            rel="noreferrer"
            variant="bordered"
            color="neutral"
            size="small"
            icon={<ExternalLinkIcon />}
            iconPosition="right"
          >
            {t('Manage')}
          </Button>
        </div>
      </div>

      <div className="account-panel__section">
        <h2>{t('Sign-in security')}</h2>
        <ul className="security-list">
          <li className="security-list__item">
            <p className="security-list__title">{t('Password')}</p>
            <p className="security-list__detail">
              {t('Managed by your sign-in provider')}
            </p>
          </li>
          <li className="security-list__item">
            <p className="security-list__title">{t('Two-step verification')}</p>
            <p className="security-list__detail">
              {t('Managed by your sign-in provider')}
            </p>
          </li>
        </ul>
      </div>
    </section>
  );
};
