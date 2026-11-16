import axios, { AxiosError } from 'axios';
import { describe, expect, it, vi } from 'vitest';

import { createApiClient, normalizeHttpError } from './client';

describe('createApiClient', () => {
  it('throws when VITE_API_URL is not set', () => {
    vi.stubEnv('VITE_API_URL', '');

    expect(() => createApiClient()).toThrow(/VITE_API_URL/);
  });
});

describe('normalizeHttpError', () => {
  it('maps an HTTP error to { message, status, details }', () => {
    const axiosError = new AxiosError(
      'Request failed with status code 404',
      'ERR_BAD_REQUEST',
      undefined,
      undefined,
      {
        status: 404,
        statusText: 'Not Found',
        headers: {},
        config: { headers: new axios.AxiosHeaders() },
        data: { detail: 'Programa no encontrado' },
      },
    );

    expect(normalizeHttpError(axiosError)).toEqual({
      message: 'Programa no encontrado',
      status: 404,
      details: { detail: 'Programa no encontrado' },
    });
  });
});
