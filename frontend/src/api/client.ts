import axios, {
  type AxiosError,
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios';

/**
 * Normalized HTTP error shape returned by the API client.
 *
 * Failed responses are rejected with this shape from the response interceptor
 * so UI and services do not depend on `AxiosError` or raw backend payloads.
 *
 * - `message`: human-readable text for the user or logs.
 * - `status`: HTTP status code (0 when there is no response, e.g. network).
 * - `details`: optional server error body or extra context.
 */
export interface ApiError {
  message: string;
  status: number;
  details?: unknown;
}

function readApiBaseUrl(): string {
  const baseUrl = import.meta.env.VITE_API_URL;
  if (!baseUrl) {
    throw new Error(
      'VITE_API_URL is not defined. Set it in the Vite environment.',
    );
  }
  return baseUrl;
}

export function normalizeHttpError(error: unknown): ApiError {
  if (!axios.isAxiosError(error)) {
    const message =
      error instanceof Error ? error.message : 'Unknown request error';
    return { message, status: 0 };
  }

  const axiosError = error as AxiosError<unknown>;
  if (!axiosError.response) {
    return {
      message: axiosError.message || 'Could not connect to the server',
      status: 0,
    };
  }

  const { status, data } = axiosError.response;
  let message = axiosError.message;
  let details: unknown = data;

  if (typeof data === 'string' && data.length > 0) {
    message = data;
  } else if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>;
    if (typeof record.message === 'string') {
      message = record.message;
    } else if (typeof record.detail === 'string') {
      message = record.detail;
    } else if (record.detail !== undefined) {
      message = 'The request could not be completed';
      details = record.detail;
    }
  }

  return { message, status, details };
}

function onRequest(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
  // Hook for Authorization; token source will be wired up with login.
  return config;
}

function onResponseSuccess(response: AxiosResponse): AxiosResponse {
  return response;
}

function onResponseError(error: unknown): Promise<never> {
  return Promise.reject(normalizeHttpError(error));
}

export function createApiClient(baseURL?: string): AxiosInstance {
  const client = axios.create({
    baseURL: baseURL ?? readApiBaseUrl(),
    headers: {
      'Content-Type': 'application/json',
    },
  });

  client.interceptors.request.use(onRequest);
  client.interceptors.response.use(onResponseSuccess, onResponseError);

  return client;
}

export const apiClient = createApiClient();
