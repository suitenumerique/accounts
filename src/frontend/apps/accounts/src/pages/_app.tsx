import { createContext, useContext, useState } from "react";
import type { AppProps } from "next/app";
import Head from "next/head";
import { CunninghamProvider } from "@gouvfr-lasuite/ui-kit";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import "../styles/globals.scss";
import "@/i18n/initI18n";
import { useLocales } from "@/i18n/useLocale";
import { ConfigProvider } from "@/features/config/ConfigProvider";
import { Auth } from "@/features/auth/Auth";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

export interface AppContextType {
  theme: string;
  setTheme: (theme: string) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within an AppContextProvider");
  }
  return context;
};

export default function MyApp(props: AppProps) {
  const [theme, setTheme] = useState<string>("dsfr-light");

  return (
    <AppContext.Provider value={{ theme, setTheme }}>
      <QueryClientProvider client={queryClient}>
        <MyAppInner {...props} />
      </QueryClientProvider>
    </AppContext.Provider>
  );
}

function MyAppInner({ Component, pageProps }: AppProps) {
  const locale = useLocales();
  const { theme } = useAppContext();

  return (
    <>
      <Head>
        <title>La Suite Account</title>
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>
      <CunninghamProvider currentLocale={locale} theme={theme}>
        <ConfigProvider>
          <Auth>
            <Component {...pageProps} />
          </Auth>
        </ConfigProvider>
      </CunninghamProvider>
    </>
  );
}
