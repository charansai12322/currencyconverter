/**
 * Centralized API client service for Moneta Currency Converter.
 */

import {
  ConvertRequest,
  ConvertResponse,
  CurrenciesResponse,
  CurrencyApiError,
  HealthResponse,
} from '../types/currency';

// Normalize base URL, removing trailing slashes
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;
export const API_BASE_URL = rawBaseUrl ? rawBaseUrl.replace(/\/+$/, '') : '';

/**
 * Handle API responses and throw strongly-typed CurrencyApiError on failure.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  const isJson = response.headers.get('content-type')?.includes('application/json');
  let data: any = null;

  if (isJson) {
    try {
      data = await response.json();
    } catch {
      // Body was not valid JSON
    }
  }

  if (!response.ok) {
    const errorMessage = data?.error || data?.detail?.error || `Request failed with status ${response.status}`;
    const errorDetails = data?.details || data?.detail?.details || (typeof data?.detail === 'string' ? data.detail : undefined);
    throw new CurrencyApiError(errorMessage, response.status, errorDetails);
  }

  return data as T;
}

/**
 * Check backend process health status.
 */
export async function checkHealth(signal?: AbortSignal): Promise<HealthResponse> {
  try {
    const url = `${API_BASE_URL}/health`;
    const response = await fetch(url, { signal });
    return await handleResponse<HealthResponse>(response);
  } catch (err: unknown) {
    if (err instanceof CurrencyApiError) throw err;
    if ((err as Error)?.name === 'AbortError') throw err;
    throw new CurrencyApiError(
      'Cannot connect to backend server. Ensure the backend process is running.',
      0,
      (err as Error)?.message
    );
  }
}

/**
 * Fetch authoritative list of supported currency codes.
 */
export async function getSupportedCurrencies(signal?: AbortSignal): Promise<CurrenciesResponse> {
  try {
    const url = `${API_BASE_URL}/api/currencies`;
    const response = await fetch(url, { signal });
    return await handleResponse<CurrenciesResponse>(response);
  } catch (err: unknown) {
    if (err instanceof CurrencyApiError) throw err;
    if ((err as Error)?.name === 'AbortError') throw err;
    throw new CurrencyApiError(
      'Failed to load supported currency list.',
      0,
      (err as Error)?.message
    );
  }
}

/**
 * Execute currency conversion request against live backend.
 */
export async function convertCurrency(
  payload: ConvertRequest,
  signal?: AbortSignal
): Promise<ConvertResponse> {
  try {
    const url = `${API_BASE_URL}/api/convert`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal,
    });
    return await handleResponse<ConvertResponse>(response);
  } catch (err: unknown) {
    if (err instanceof CurrencyApiError) throw err;
    if ((err as Error)?.name === 'AbortError') throw err;
    throw new CurrencyApiError(
      'Conversion request failed. Please check your connection and try again.',
      0,
      (err as Error)?.message
    );
  }
}
