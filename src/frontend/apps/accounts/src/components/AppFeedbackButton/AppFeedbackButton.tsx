'use client';

import { Button } from '@gouvfr-lasuite/cunningham-react';
import { QuestionMark } from '@gouvfr-lasuite/ui-kit/icons';
import { useTranslation } from 'react-i18next';

import { useConfig } from '@/features/config/ConfigProvider';

export const AppFeedbackButton = ({ url }: { url: string }) => {
  const { t } = useTranslation();

  return (
    <Button
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      color="error"
      variant="secondary"
      size="small"
      icon={<QuestionMark aria-hidden size={20} />}
    >
      {t('Give feedback')}
    </Button>
  );
};

export const useFeedbackFormUrl = () =>
  useConfig().config.FRONTEND_FEEDBACK_FORM_URL;
