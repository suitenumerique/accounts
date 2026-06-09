/**
 * Public configuration exposed by the backend at `GET /api/v1.0/config/`.
 * Only the fields actually consumed by the frontend are typed here.
 */
export interface Config {
  ENVIRONMENT?: string;
  LANGUAGES: [string, string][];
  LANGUAGE_CODE: string;
  FRONTEND_THEME?: string;
  FRONTEND_CSS_URL?: string;
  FRONTEND_JS_URL?: string;
  FRONTEND_SILENT_LOGIN_ENABLED?: boolean;
}
