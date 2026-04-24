import { useTranslation } from 'react-i18next';

import { Text } from '@/components/';

type TitleSemanticsProps = {
  headingLevel?: 'h1' | 'h2' | 'h3';
  className?: string;
};

export const Title = ({
  headingLevel = 'h2',
  className,
}: TitleSemanticsProps) => {
  const { t } = useTranslation();

  return (
    <Text
      className={`--accounts--title${className ? ` ${className}` : ''}`}
      $direction="row"
      $align="center"
      $margin="none"
      as={headingLevel}
      $zIndex={1}
      $size="1.375rem"
      $color="var(--c--contextuals--content--logo1)"
    >
      {t('My Account')}
    </Text>
  );
};
