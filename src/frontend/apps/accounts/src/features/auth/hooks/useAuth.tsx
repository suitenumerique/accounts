import { useRouter } from 'next/router';
import { useEffect, useRef, useState } from 'react';

import { useAnalytics } from '@/libs';

import { useAuthQuery } from '../api';

const regexpUrlsAuth = [/\/docs\/$/g, /\/docs$/g, /^\/$/g];

export const useAuth = () => {
  const { data: user, ...authStates } = useAuthQuery();
  const { pathname } = useRouter();
  const { trackEvent } = useAnalytics();
  const [hasTracked, setHasTracked] = useState(authStates.isFetched);
  const isAuthLoading =
    authStates.fetchStatus !== 'idle' || authStates.isLoading;
  const hasInitiallyLoaded = useRef(false);
  if (authStates.isFetched) {
    hasInitiallyLoaded.current = true;
  }
  const [pathAllowed, setPathAllowed] = useState<boolean>(
    !regexpUrlsAuth.some((regexp) => !!pathname.match(regexp)),
  );

  useEffect(() => {
    setPathAllowed(!regexpUrlsAuth.some((regexp) => !!pathname.match(regexp)));
  }, [pathname]);

  useEffect(() => {
    if (!hasTracked && user && authStates.isSuccess) {
      trackEvent({
        eventName: 'user',
        id: user?.id || '',
        email: user?.email || '',
      });
      setHasTracked(true);
    }
  }, [hasTracked, authStates.isSuccess, user, trackEvent]);

  return {
    user,
    authenticated: !!user && authStates.isSuccess,
    pathAllowed,
    hasInitiallyLoaded: hasInitiallyLoaded.current,
    isAuthLoading,
    ...authStates,
  };
};
