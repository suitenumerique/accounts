import { Button } from '@gouvfr-lasuite/cunningham-react';
import Image from 'next/image';
import { useTranslation } from 'react-i18next';
import { css } from 'styled-components';

import { Box, Icon, Text } from '@/components';
import { useConfig } from '@/core';
import { useCunninghamTheme } from '@/cunningham';
import { ProConnectButton, gotoLogin } from '@/features/auth';
import { useResponsiveStore } from '@/stores';

import banner from '../assets/banner.jpg';

import { getHeaderHeight } from './HomeHeader';

export default function HomeBanner() {
  const { t } = useTranslation();
  const { spacingsTokens } = useCunninghamTheme();
  const { isMobile, isSmallMobile } = useResponsiveStore();
  const { data: config } = useConfig();
  const withProConnect = config?.theme_customization?.home?.['with-proconnect'];
  const icon = config?.theme_customization?.home?.['icon-banner'];

  return (
    <Box
      $maxWidth="78rem"
      $width="100%"
      $justify="space-around"
      $align="center"
      $height="100vh"
      $margin={{ top: `-${getHeaderHeight(isSmallMobile)}px` }}
      $position="relative"
      className="--accounts--home-banner"
    >
      <Box
        $width="100%"
        $justify="center"
        $align="center"
        $position="relative"
        $direction={!isMobile ? 'row' : 'column'}
        $gap="1rem"
        $overflow="auto"
        $css="flex-basis: 70%;"
      >
        <Box
          $width={!isMobile ? '50%' : '100%'}
          $justify="center"
          $align="center"
          $gap={spacingsTokens['sm']}
        >
          {icon?.src && (
            <Image
              data-testid="header-icon-docs"
              width={0}
              height={0}
              style={{
                width: '64px',
                height: 'auto',
              }}
              priority
              {...icon}
            />
          )}
          <Text
            as="h2"
            $size={!isMobile ? 'xs-alt' : '2.3rem'}
            $weight="bold"
            $textAlign="center"
            $margin="none"
            $css={css`
              line-height: ${!isMobile ? '56px' : '45px'};
            `}
          >
            {t('My Account, your gateway to the collaborative suite.')}
          </Text>
          <Text
            $size="lg"
            $textAlign="center"
            $margin={{ bottom: 'small' }}
            $variation="secondary"
          >
            {t(
              'Login to La Suite collaborative tools from one place. Soon, you will also be able to manage your account information here.',
            )}
          </Text>
          {withProConnect ? (
            <ProConnectButton />
          ) : (
            <Button
              onClick={() => gotoLogin()}
              icon={<Icon iconName="bolt" $color="white" />}
            >
              {t('Login')}
            </Button>
          )}
        </Box>
        {!isMobile && (
          <Image
            src={banner}
            alt={t('Banner image')}
            priority
            style={{
              width: 'auto',
              maxWidth: '100%',
              height: 'fit-content',
              overflow: 'auto',
              maxHeight: '100%',
            }}
          />
        )}
      </Box>
      <Box $css="bottom: 3rem" $position="absolute">
        <Button
          color="brand"
          variant="secondary"
          icon={<Icon $color="inherit" iconName="expand_more" />}
          onClick={(e) => {
            e.preventDefault();
            document
              .querySelector('#accounts-app-info')
              ?.scrollIntoView({ behavior: 'smooth' });
          }}
        >
          {t('Show more')}
        </Button>
      </Box>
    </Box>
  );
}
