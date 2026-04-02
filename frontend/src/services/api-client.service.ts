// Base API client for making HTTP requests to the backend
// Provides security features: CSRF protection, auth token injection,
// request timeout, and structured error handling.

import { ApiException, type RequestConfig } from "./api-types";

/**
 * Resolved base URL for all API calls.
 * - In development the CRA proxy forwards /api → backend:8000
 * - In production Nginx (or the API gateway) does the same
 * So we always use a relative path; no hard-coded host.
 */
const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL ?? "/api/v1";

/** Default timeout for every request (ms). */
const DEFAULT_TIMEOUT_MS = 30_000;

/** Maximum retries for transient (5xx / network) errors. */
const MAX_RETRIES = 2;
const RETRY_BACKOFF_MS = 500;

// ---------------------------------------------------------------------------
// Token helpers
// ---------------------------------------------------------------------------

let accessToken: string | null =
  typeof window !== "undefined"
    ? window.localStorage.getItem("accessToken")
    : null;

/** Called by the auth layer after login / token refresh. */
export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

/** Access token present and not past stored expiry (if any). */
export function hasValidOfficialSession(): boolean {
  if (!accessToken) return false;
  if (typeof window === "undefined") return true;

  const exp = window.localStorage.getItem("accessTokenExpiresAt");
  if (exp === null) return true;

  const expMs = Number(exp);
  if (Number.isNaN(expMs)) return true;

  return Date.now() < expMs;
}

export function clearAuthSession(): void {
  accessToken = null;

  if (typeof window === "undefined") return;

  window.localStorage.removeItem("accessToken");
  window.localStorage.removeItem("refreshToken");
  window.localStorage.removeItem("tokenType");
  window.localStorage.removeItem("accessTokenExpiresAt");
}

/** Read the XSRF-TOKEN cookie set by the backend. */
function readCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)XSRF-TOKEN=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

// ---------------------------------------------------------------------------
// Core request function
// ---------------------------------------------------------------------------

async function request<T>(
  endpoint: string,
  config: RequestConfig = {},
): Promise<T> {
  const { method = "GET", headers = {}, params, body, omitAuth = false } = config;

  // Build URL with query params
  let url = `${API_BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value));
      }
    }
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  // Assemble headers
  const reqHeaders: Record<string, string> = {
    Accept: "application/json",
    ...headers,
  };

  // Inject auth token (skip for anonymous public reads)
  if (accessToken && !omitAuth) {
    reqHeaders["Authorization"] = `Bearer ${accessToken}`;
  }

  // Inject CSRF token for mutating methods
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = readCsrfToken();
    if (csrf) {
      reqHeaders["X-XSRF-TOKEN"] = csrf;
    }
    if (body !== undefined && !(body instanceof FormData)) {
      reqHeaders["Content-Type"] = "application/json";
    }
  }

  const fetchOptions: RequestInit = {
    method,
    headers: reqHeaders,
    credentials: "same-origin", // send cookies to same origin only
  };

  if (body !== undefined) {
    fetchOptions.body =
      body instanceof FormData ? body : JSON.stringify(body);
  }

  // Timeout via AbortController
  const controller = new AbortController();
  fetchOptions.signal = controller.signal;
  const timeoutId = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);

  try {
    const response = await fetch(url, fetchOptions);
    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorBody: Record<string, unknown> | null = null;
      try {
        errorBody = await response.json();
      } catch {
        // response may not be JSON
      }

      throw new ApiException(
        (errorBody?.message as string) ??
          (errorBody?.detail as string) ??
          response.statusText,
        response.status,
        (errorBody?.code as string) ?? undefined,
        errorBody?.details ?? errorBody,
      );
    }

    // 204 No Content
    if (response.status === 204) return undefined as unknown as T;

    return (await response.json()) as T;
  } catch (err) {
    clearTimeout(timeoutId);

    if (err instanceof ApiException) throw err;

    // Network / abort error
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiException("Request timed out", 408, "TIMEOUT");
    }

    throw new ApiException(
      (err as Error).message ?? "Network error",
      0,
      "NETWORK_ERROR",
    );
  }
}

// ---------------------------------------------------------------------------
// Retry wrapper for idempotent / transient-safe calls
// ---------------------------------------------------------------------------

async function requestWithRetry<T>(
  endpoint: string,
  config: RequestConfig = {},
): Promise<T> {
  const method = config.method ?? "GET";
  // Only retry safe (GET) or explicitly idempotent methods
  const retryable = method === "GET";
  let lastError: unknown;

  const attempts = retryable ? MAX_RETRIES + 1 : 1;
  for (let i = 0; i < attempts; i++) {
    try {
      return await request<T>(endpoint, config);
    } catch (err) {
      lastError = err;
      const isTransient =
        err instanceof ApiException &&
        (err.statusCode >= 500 || err.statusCode === 0);
      if (!isTransient || i === attempts - 1) throw err;
      await new Promise((r) =>
        setTimeout(r, RETRY_BACKOFF_MS * Math.pow(2, i)),
      );
    }
  }
  throw lastError;
}

// ---------------------------------------------------------------------------
// Public API client
// ---------------------------------------------------------------------------

/** Options for {@link ApiClient.get} (single object avoids confusing params vs auth flags). */
export type ApiGetOptions = {
  params?: RequestConfig["params"];
  omitAuth?: boolean;
};

export class ApiClient {
  /** GET request with automatic retry on transient failures. */
  static async get<T>(endpoint: string, options?: ApiGetOptions): Promise<T> {
    return requestWithRetry<T>(endpoint, {
      method: "GET",
      params: options?.params,
      omitAuth: options?.omitAuth,
    });
  }

  /** POST request. */
  static async post<T>(
    endpoint: string,
    body?: unknown,
    config?: Omit<RequestConfig, "method" | "body">,
  ): Promise<T> {
    return request<T>(endpoint, { ...config, method: "POST", body });
  }

  /** PATCH request. */
  static async patch<T>(
    endpoint: string,
    body?: unknown,
    config?: Omit<RequestConfig, "method" | "body">,
  ): Promise<T> {
    return request<T>(endpoint, { ...config, method: "PATCH", body });
  }

  /** PUT request. */
  static async put<T>(
    endpoint: string,
    body?: unknown,
    config?: Omit<RequestConfig, "method" | "body">,
  ): Promise<T> {
    return request<T>(endpoint, { ...config, method: "PUT", body });
  }

  /** DELETE request. */
  static async delete<T>(endpoint: string): Promise<T> {
    return request<T>(endpoint, { method: "DELETE" });
  }
}
