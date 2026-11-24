/** Error carrying the API's UPPER_SNAKE_CASE code. Safe to import from client components. */
export class ApiError extends Error {
  constructor(
    public readonly code: string,
    public readonly status: number,
    public readonly detail: Record<string, unknown> = {},
  ) {
    super(code);
    this.name = "ApiError";
  }
}

/** Result shape returned by Server Actions to client components. */
export type ActionResult<T = undefined> = { ok: true; code: string; data: T } | { ok: false; code: string };
