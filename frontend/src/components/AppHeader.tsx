import React from 'react';

interface AppHeaderProps {
  backendStatus: 'online' | 'offline' | 'checking';
}

export const AppHeader: React.FC<AppHeaderProps> = ({ backendStatus }) => {
  return (
    <header className="app-header">
      <div className="brand-section">
        <h1 className="brand-wordmark">MONETA</h1>
        <p className="brand-tagline">Currency, without the noise.</p>
      </div>

      <div className="api-status-badge" title={`Backend status: ${backendStatus}`}>
        <span
          className={`status-dot ${
            backendStatus === 'online'
              ? 'online'
              : backendStatus === 'offline'
              ? 'offline'
              : ''
          }`}
        />
        <span>
          {backendStatus === 'online'
            ? 'API Online'
            : backendStatus === 'offline'
            ? 'API Offline'
            : 'Checking API'}
        </span>
      </div>
    </header>
  );
};
