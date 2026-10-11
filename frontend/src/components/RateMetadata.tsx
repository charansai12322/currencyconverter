import React from 'react';
import { ShieldCheck, Clock } from 'lucide-react';
import { ConvertResponse } from '../types/currency';

interface RateMetadataProps {
  result: ConvertResponse | null;
}

export const RateMetadata: React.FC<RateMetadataProps> = ({ result }) => {
  return (
    <footer className="rate-metadata-footer">
      <div className="meta-row">
        <div className="meta-source">
          <ShieldCheck size={14} style={{ color: 'var(--color-ink-secondary)' }} />
          <span>Rates sourced via {result?.source || 'ExchangeRate-API'}</span>
        </div>

        {result?.rate_last_updated_utc && (
          <div className="meta-timestamp">
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
              <Clock size={13} style={{ color: 'var(--color-ink-secondary)' }} />
              Provider updated: {result.rate_last_updated_utc}
            </span>
          </div>
        )}
      </div>

      <p className="disclaimer-note">
        MONETA displays reference mid-market exchange rates. Commercial rates offered by banks,
        financial institutions, or card issuers may include processing spreads and transaction fees.
      </p>
    </footer>
  );
};
