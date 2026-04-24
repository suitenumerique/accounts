import Head from 'next/head';
import type { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import { MainLayout } from '@/layouts';
import { NextPageWithLayout } from '@/types/next';

const Page: NextPageWithLayout = () => {
  const { t } = useTranslation();

  return (
    <>
      <Head>
        <title>{`${t('My Account')}`}</title>
        <meta property="og:title" content={`${t('My Account')}`} key="title" />
      </Head>
    </>
  );
};

Page.getLayout = function getLayout(page: ReactElement) {
  return <MainLayout backgroundColor="grey">{page}</MainLayout>;
};

export default Page;
