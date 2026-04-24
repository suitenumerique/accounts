import { Button } from '@gouvfr-lasuite/cunningham-react';
import { Trans, useTranslation } from 'react-i18next';
import { css } from 'styled-components';

import { Box, Text } from '@/components';
import { Footer } from '@/features/footer';
import { MAIN_LAYOUT_ID } from '@/layouts/conf';
import { useResponsiveStore } from '@/stores';

import SC5 from '../assets/SC5.png';
import GithubIcon from '../assets/github.svg';

import HomeBanner from './HomeBanner';
import { HomeBottom } from './HomeBottom';
import { HomeHeader, getHeaderHeight } from './HomeHeader';
import { HomeSection } from './HomeSection';

export function HomeContent() {
  const { t } = useTranslation();
  const { isMobile, isSmallMobile, isTablet } = useResponsiveStore();

  return (
    <Box
      as="main"
      role="main"
      id={MAIN_LAYOUT_ID}
      tabIndex={-1}
      className="--accounts--home-content"
      aria-label={t('Main content')}
      $css={css`
        &:focus {
          outline: 3px solid var(--c--contextuals--border--surface--primary);
          outline-offset: -3px;
        }

        &:focus:not(:focus-visible) {
          outline: none;
        }
      `}
    >
      <HomeHeader />
      <Box
        $css={css`
          height: calc(100vh - ${getHeaderHeight(isSmallMobile)}px);
          overflow-y: auto;
        `}
      >
        <Box
          $align="center"
          $justify="center"
          $maxWidth="1120px"
          $padding={{ horizontal: isSmallMobile ? '1rem' : '3rem' }}
          $width="100%"
          $margin="auto"
        >
          <HomeBanner />
          <Box
            id="accounts-app-info"
            $maxWidth="100%"
            $gap={isMobile ? '115px' : '230px'}
            $padding={{ bottom: '3rem' }}
          >
            <Box $gap={isMobile ? '115px' : '30px'}>
              <HomeSection
                isColumn={false}
                isSmallDevice={isTablet}
                illustration={SC5}
                title={t('Govs ❤️ Open Source.')}
                tag={t('Open Source')}
                textWidth="60%"
                $css={`min-height: calc(100vh - ${getHeaderHeight(isSmallMobile)}px);`}
                description={
                  <Box>
                    <Box
                      $css={css`
                        & a {
                          color: inherit;
                        }
                      `}
                    >
                      <Text as="p" $display="inline" $variation="secondary">
                        <Trans
                          t={t}
                          i18nKey="home-content-mon-compte-open-source-part1"
                          defaults="My Account is the entry point to La Suite collaborative tools. It is built on top of <0>Django Rest Framework</0> and <1>Next.js</1>."
                          components={[
                            <a
                              key="django-rest-framework"
                              href="https://www.django-rest-framework.org/"
                              target="_blank"
                            />,
                            <a
                              key="next-js"
                              href="https://nextjs.org/"
                              target="_blank"
                            />,
                          ]}
                        />
                      </Text>
                      <Text as="p" $display="inline">
                        <Trans
                          t={t}
                          i18nKey="home-content-mon-compte-open-source-part2"
                          defaults="You can easily self-host My Account (check our installation <0>documentation</0>). Today it centralizes access to services, and tomorrow it will also help manage account information.<2/>Mon compte uses an innovation and business friendly <1>licence</1> (MIT)."
                          components={[
                            <a
                              key="documentation"
                              href="https://github.com/suitenumerique/accounts/"
                              target="_blank"
                            />,
                            <a
                              key="licence"
                              href="https://github.com/suitenumerique/accounts/blob/main/LICENSE"
                              target="_blank"
                            />,
                            <br key="line-break" />,
                          ]}
                        />
                      </Text>
                    </Box>
                    <Box
                      $direction="row"
                      $gap="1rem"
                      $margin={{ top: 'small' }}
                    >
                      <Button
                        color="neutral"
                        variant="secondary"
                        icon={<GithubIcon />}
                        href="https://github.com/suitenumerique/accounts"
                        target="_blank"
                      >
                        GitHub
                      </Button>
                    </Box>
                  </Box>
                }
              />
            </Box>
            <HomeBottom />
          </Box>
        </Box>
        <Footer />
      </Box>
    </Box>
  );
}
