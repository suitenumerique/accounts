import React, {
  PropsWithChildren,
  useCallback,
  useEffect,
  useState,
} from "react";
import { Spinner } from "@gouvfr-lasuite/ui-kit";

import { fetchAPI } from "@/features/api/fetchApi";
import { User } from "./types";
import { LOGIN_URL, LOGOUT_URL } from "./conf";

export const login = () => {
  window.location.replace(LOGIN_URL);
};

export const logout = () => {
  window.location.replace(LOGOUT_URL);
};

interface AuthContextInterface {
  user?: User | null;
  refreshUser?: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextInterface>({});

export const useAuth = () => React.useContext(AuthContext);

export const Auth = ({ children }: PropsWithChildren) => {
  const [user, setUser] = useState<User | null>();

  const loadUser = useCallback(async () => {
    try {
      const response = await fetchAPI("users/me/");
      return (await response.json()) as User;
    } catch {
      return null;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    setUser(await loadUser());
  }, [loadUser]);

  useEffect(() => {
    let isMounted = true;

    void loadUser().then((nextUser) => {
      if (isMounted) {
        setUser(nextUser);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [loadUser]);

  if (user === undefined) {
    return (
      <div className="global-loader">
        <Spinner size="xl" />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};
