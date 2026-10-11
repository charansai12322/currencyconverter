import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Search } from 'lucide-react';

interface CurrencySelectProps {
  label: string;
  value: string;
  currencies: string[];
  onChange: (code: string) => void;
  disabled?: boolean;
  isLoading?: boolean;
}

export const CurrencySelect: React.FC<CurrencySelectProps> = ({
  label,
  value,
  currencies,
  onChange,
  disabled = false,
  isLoading = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input on open
  useEffect(() => {
    if (isOpen) {
      setSearch('');
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    }
  }, [isOpen]);

  const filteredCurrencies = currencies.filter((code) =>
    code.toLowerCase().includes(search.toLowerCase().trim())
  );

  const handleSelect = (code: string) => {
    onChange(code);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div className="field-group" ref={containerRef} onKeyDown={handleKeyDown}>
      <label className="field-label">{label}</label>
      <div className="currency-selector-container">
        <button
          type="button"
          className={`selector-trigger ${isOpen ? 'is-open' : ''}`}
          onClick={() => !disabled && setIsOpen(!isOpen)}
          disabled={disabled || isLoading}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          aria-label={`${label} selector, current value is ${value}`}
        >
          <span className="currency-code-badge">{isLoading ? '...' : value}</span>
          <ChevronDown size={16} strokeWidth={2.2} style={{ opacity: 0.6 }} />
        </button>

        {isOpen && (
          <div className="selector-dropdown" role="listbox">
            <div className="dropdown-search-wrap">
              <Search size={14} strokeWidth={2} style={{ color: 'var(--color-ink-secondary)' }} />
              <input
                ref={searchInputRef}
                type="text"
                className="dropdown-search-input"
                placeholder="Search ISO code..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                autoComplete="off"
              />
            </div>
            <ul className="dropdown-list">
              {filteredCurrencies.length > 0 ? (
                filteredCurrencies.map((code) => (
                  <li
                    key={code}
                    role="option"
                    aria-selected={code === value}
                    className={`dropdown-item ${code === value ? 'is-selected' : ''}`}
                    onClick={() => handleSelect(code)}
                  >
                    <span>{code}</span>
                    {code === value && <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>✓</span>}
                  </li>
                ))
              ) : (
                <li className="dropdown-empty">No currency matching "{search}"</li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
