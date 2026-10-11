/**
 * TypeScript contract interfaces mirroring the FastAPI backend schemas.
 */

export interface ConvertRequest {
  amount: number;
  from_currency: string;
  to_currency: string;
}

export interface ConvertResponse {
  success: boolean;
  amount: number;
  from_currency: string;
  to_currency: string;
  exchange_rate: number;
  converted_amount: number;
  rate_last_updated_utc: string | null;
  rate_next_update_utc: string | null;
  source: string;
}

export interface CurrenciesResponse {
  success: boolean;
  count: number;
  base_currency: string;
  currencies: string[];
}

export interface HealthResponse {
  status: string;
  environment: string;
  version: string;
}

export interface ApiErrorPayload {
  success: boolean;
  error: string;
  details?: string;
}

export class CurrencyApiError extends Error {
  public statusCode: number;
  public details?: string;

  constructor(message: string, statusCode: number, details?: string) {
    super(message);
    this.name = 'CurrencyApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}
