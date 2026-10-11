import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorBannerProps {
  title: string;
  details?: string;
  onRetry?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ title, details, onRetry }) => {
  return (
    <div className="error-banner" role="alert">
      <AlertCircle size={18} strokeWidth={2} style={{ flexShrink: 0, marginTop: '2px' }} />
      <div style={{ flex: 1 }}>
        <p className="error-title">{title}</p>
        {details && <p className="error-details">{details}</p>}
      </div>
      {onRetry && (
        <button type="button" className="retry-btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
};
