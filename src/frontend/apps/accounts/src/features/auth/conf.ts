import { baseApiUrl } from '@/api';

export const HOME_URL = '/home/';
export const LOGIN_URL = `${baseApiUrl()}oidc/authenticate/`;
export const LOGOUT_URL = `${baseApiUrl()}oidc/logout/`;
export const PATH_AUTH_SESSION_STORAGE = 'accounts-path-auth';
export const SILENT_LOGIN_RETRY = 'silent-login-retry';
