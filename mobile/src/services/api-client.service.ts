/**
 * HTTP client for the e-voting backend.
 * Simplified version of the web frontend's ApiClient.
 */

import Constants from "expo-constants";

const API_BASE_URL =
  Constants.expoConfig?.extra?.apiBaseUrl ?? "https://localhost/api/v1";

const TIMEOUT_MS = 30_000;

export class ApiException extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
  ) {
    super(message);
    this.name = "ApiException";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      let body: any = null;
      try { body = await response.json(); } catch {}
      throw new ApiException(
        body?.message ?? body?.detail ?? response.statusText,
        response.status,
        body?.code,
      );
    }

    if (response.status === 204) return undefined as unknown as T;
    return (await response.json()) as T;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof ApiException) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiException("Request timed out", 408, "TIMEOUT");
    }
    throw new ApiException((err as Error).message ?? "Network error", 0, "NETWORK_ERROR");
  }
}

export const ApiClient = {
  get: <T>(endpoint: string) => request<T>(endpoint, { method: "GET" }),
  post: <T>(endpoint: string, body?: unknown) =>
    request<T>(endpoint, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  delete: (endpoint: string) => request<void>(endpoint, { method: "DELETE" }),
};
