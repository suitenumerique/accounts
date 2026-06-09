import { baseApiUrl, isJson } from "./utils";
import { APIError } from "./APIError";

/**
 * Retrieves the CSRF token from the document's cookies.
 */
function getCSRFToken() {
  return document.cookie
    .split(";")
    .filter((cookie) => cookie.trim().startsWith("csrftoken="))
    .map((cookie) => cookie.split("=")[1])
    .pop();
}

export const fetchAPI = async (input: string, init?: RequestInit) => {
  const apiUrl = `${baseApiUrl()}${input}`;
  const csrfToken = getCSRFToken();

  const response = await fetch(apiUrl, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
      ...(csrfToken && { "X-CSRFToken": csrfToken }),
    },
  });

  if (response.ok) {
    return response;
  }

  const data = await response.text();

  if (isJson(data)) {
    throw new APIError(response.status, JSON.parse(data));
  }

  throw new APIError(response.status);
};
