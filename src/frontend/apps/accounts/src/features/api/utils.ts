export const getOrigin = () => {
  return (
    process.env.NEXT_PUBLIC_API_ORIGIN ||
    (typeof window !== "undefined" ? window.location.origin : "")
  );
};

export const baseApiUrl = (apiVersion: string = "1.0") => {
  return `${getOrigin()}/api/v${apiVersion}/`;
};

export const isJson = (str: string) => {
  try {
    JSON.parse(str);
  } catch {
    return false;
  }
  return true;
};
