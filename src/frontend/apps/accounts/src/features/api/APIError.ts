export class APIError extends Error {
  data?: unknown;
  code: number;

  constructor(code: number, data?: unknown) {
    super(`API error ${code}`);
    this.name = "APIError";
    this.code = code;
    this.data = data;
  }
}
