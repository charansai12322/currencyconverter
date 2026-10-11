import React from 'react';
import { ConvertResponse } from '../types/currency';

interface ConversionResultProps {
  result: ConvertResponse | null;
  isLoading: boolean;
  isStale: boolean;
}

export const ConversionResult: React.FC<ConversionResultProps> = ({
  result,
  isLoading,
  isStale,
}) => {
  if (isLoading) {
    return (
      <div className="result-surface" aria-live="polite" aria-busy="true">
        <div className="skeleton-line skeleton-title" />
        <div className="skeleton-line skeleton-amount" />
        <div className="skeleton-line skeleton-meta" />
      </div>
    );
  }

  if (!result) {
    return null;
  }

  // Format converted amount with international locale formatting for readability
  const formattedConverted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(result.converted_amount);

  return (
    <div
      className="result-surface"
      aria-live="polite"
      style={{ opacity: isStale ? 0.6 : 1, transition: 'opacity 0.2s ease' }}
    >
      <div className="result-header">
        <span className="result-eyebrow">
          {isStale ? 'Previous Conversion (Stale)' : 'Converted Total'}
        </span>
        {isStale && (
          <span style={{ fontSize: '0.6875rem', color: 'var(--color-ink-secondary)', fontWeight: 500 }}>
            Inputs updated — press Convert
          </span>
        )}
      </div>

      <div className="result-amount-display tabular-nums">
        <span>{formattedConverted}</span>
        <span className="result-currency-code">{result.to_currency}</span>
      </div>

      <div className="result-rate-summary tabular-nums">
        <span>
          1 {result.from_currency} = {result.exchange_rate} {result.to_currency}
        </span>
      </div>
    </div>
  );
};
