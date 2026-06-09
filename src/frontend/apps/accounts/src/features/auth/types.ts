/**
 * Current user as returned by `GET /api/v1.0/users/me/`.
 */
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  short_name: string | null;
  language: string | null;
}
