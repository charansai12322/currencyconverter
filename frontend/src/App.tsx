import React, { useState, useEffect, useRef } from 'react';
import { Loader2, ArrowRight } from 'lucide-react';
import { AppHeader } from './components/AppHeader';
import { CurrencyField } from './components/CurrencyField';
import { CurrencySelect } from './components/CurrencySelect';
import { SwapButton } from './components/SwapButton';
import { ConversionResult } from './components/ConversionResult';
import { RateMetadata } from './components/RateMetadata';
import { ErrorBanner } from './components/ErrorBanner';
import {
  checkHealth,
  getSupportedCurrencies,
  convertCurrency,
} from './services/currencyApi';
import { ConvertResponse, CurrencyApiError } from './types/currency';

export const App: React.FC = () => {
  // Form input state
  const [amount, setAmount] = useState<string>('100');
  const [fromCurrency, setFromCurrency] = useState<string>('USD');
  const [toCurrency, setToCurrency] = useState<string>('INR');

  // Currencies & backend status
  const [currencies, setCurrencies] = useState<string[]>([]);
  const [isLoadingCurrencies, setIsLoadingCurrencies] = useState<boolean>(true);
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  // Conversion result & loading state
  const [result, setResult] = useState<ConvertResponse | null>(null);
  const [isConverting, setIsConverting] = useState<boolean>(false);
  const [lastConvertedParams, setLastConvertedParams] = useState<{
    amount: number;
    from: string;
    to: string;
  } | null>(null);

  // Error handling
  const [error, setError] = useState<{ title: string; details?: string } | null>(null);

  // Active conversion abort controller
  const abortControllerRef = useRef<AbortController | null>(null);

  // Initial load: check health and populate currencies
  useEffect(() => {
    let isMounted = true;

    async function initialize() {
      try {
        // 1. Health check
        const health = await checkHealth();
        if (isMounted) {
          setBackendStatus(health.status === 'healthy' ? 'online' : 'offline');
        }
      } catch {
        if (isMounted) {
          setBackendStatus('offline');
        }
      }

      try {
        // 2. Load supported currencies
        setIsLoadingCurrencies(true);
        const data = await getSupportedCurrencies();
        if (isMounted && data.currencies && data.currencies.length > 0) {
          setCurrencies(data.currencies);
          // Set sensible defaults if available
          if (data.currencies.includes('USD')) setFromCurrency('USD');
          if (data.currencies.includes('INR')) setToCurrency('INR');
        }
      } catch (err: unknown) {
        if (isMounted) {
          const apiErr = err as CurrencyApiError;
          setError({
            title: 'Failed to load currency list',
            details: apiErr.details || 'Please ensure the backend API is online and refresh.',
          });
        }
      } finally {
        if (isMounted) {
          setIsLoadingCurrencies(false);
        }
      }
    }

    initialize();

    return () => {
      isMounted = false;
    };
  }, []);

  // Compute whether current form inputs differ from the last successful conversion
  const parsedAmount = parseFloat(amount);
  const isStale = Boolean(
    result &&
      lastConvertedParams &&
      (!parsedAmount ||
        parsedAmount !== lastConvertedParams.amount ||
        fromCurrency !== lastConvertedParams.from ||
        toCurrency !== lastConvertedParams.to)
  );

  // Handle conversion execution
  const handleConvert = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    // Validation
    const numericAmount = parseFloat(amount);
    if (isNaN(numericAmount) || numericAmount < 0) {
      setError({
        title: 'Invalid Amount',
        details: 'Please enter a valid non-negative numeric amount.',
      });
      return;
    }

    if (!fromCurrency || !toCurrency) {
      setError({
        title: 'Missing Currency',
        details: 'Please select both source and target currencies.',
      });
      return;
    }

    // Abort previous in-flight request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsConverting(true);
    setError(null);

    try {
      const response = await convertCurrency(
        {
          amount: numericAmount,
          from_currency: fromCurrency,
          to_currency: toCurrency,
        },
        controller.signal
      );

      setResult(response);
      setLastConvertedParams({
        amount: numericAmount,
        from: fromCurrency,
        to: toCurrency,
      });
    } catch (err: unknown) {
      if ((err as Error)?.name === 'AbortError') {
        return; // Request was aborted by newer submission
      }
      const apiErr = err as CurrencyApiError;
      setError({
        title: apiErr.message || 'Conversion Error',
        details: apiErr.details,
      });
    } finally {
      setIsConverting(false);
    }
  };

  // Swap currencies
  const handleSwap = () => {
    const prevFrom = fromCurrency;
    const prevTo = toCurrency;
    setFromCurrency(prevTo);
    setToCurrency(prevFrom);
  };

  return (
    <div className="moneta-container">
      <AppHeader backendStatus={backendStatus} />

      <main>
        <div className="instrument-card">
          {/* Signature Interaction: The Rate Transfer indicator */}
          {isConverting && (
            <div className="transfer-line-container">
              <div className="transfer-line-pulse" />
            </div>
          )}

          <form onSubmit={handleConvert}>
            <div className="input-grid">
              {/* Monetary Amount Input */}
              <CurrencyField
                amount={amount}
                currency={fromCurrency}
                onChange={(val) => {
                  setAmount(val);
                  if (error) setError(null);
                }}
                disabled={isConverting}
              />

              {/* Currency Selectors & Swap Control */}
              <div className="currencies-pair-row">
                <CurrencySelect
                  label="From Currency"
                  value={fromCurrency}
                  currencies={currencies}
                  onChange={(code) => {
                    setFromCurrency(code);
                    if (error) setError(null);
                  }}
                  disabled={isConverting}
                  isLoading={isLoadingCurrencies}
                />

                <SwapButton onSwap={handleSwap} disabled={isConverting || isLoadingCurrencies} />

                <CurrencySelect
                  label="To Currency"
                  value={toCurrency}
                  currencies={currencies}
                  onChange={(code) => {
                    setToCurrency(code);
                    if (error) setError(null);
                  }}
                  disabled={isConverting}
                  isLoading={isLoadingCurrencies}
                />
              </div>
            </div>

            {/* Primary Action Button */}
            <div className="action-row">
              <button
                type="submit"
                className="primary-convert-btn"
                disabled={isConverting || isLoadingCurrencies || !amount || parseFloat(amount) < 0}
              >
                {isConverting ? (
                  <>
                    <Loader2 size={18} className="spinner" />
                    <span>Fetching live rate...</span>
                  </>
                ) : (
                  <>
                    <span>Convert {fromCurrency} to {toCurrency}</span>
                    <ArrowRight size={17} strokeWidth={2.2} />
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Contextual Error Banner */}
          {error && (
            <ErrorBanner
              title={error.title}
              details={error.details}
              onRetry={() => handleConvert()}
            />
          )}

          {/* Real Conversion Result */}
          <ConversionResult
            result={result}
            isLoading={isConverting}
            isStale={isStale}
          />
        </div>

        {/* Real Rate Metadata & Disclaimer */}
        <RateMetadata result={result} />
      </main>
    </div>
  );
};
