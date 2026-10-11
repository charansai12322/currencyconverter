import React from 'react';

interface CurrencyFieldProps {
  amount: string;
  currency: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export const CurrencyField: React.FC<CurrencyFieldProps> = ({
  amount,
  currency,
  onChange,
  disabled = false,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    // Allow empty or positive numeric with at most one decimal point
    if (val === '' || /^\d*\.?\d*$/.test(val)) {
      onChange(val);
    }
  };

  return (
    <div className="field-group">
      <div className="field-header">
        <label htmlFor="amount-input" className="field-label">
          Amount to Convert ({currency})
        </label>
      </div>
      <div className="amount-input-row">
        <input
          id="amount-input"
          type="text"
          inputMode="decimal"
          className="amount-input tabular-nums"
          placeholder="0.00"
          value={amount}
          onChange={handleChange}
          disabled={disabled}
          autoComplete="off"
          spellCheck={false}
          aria-label="Monetary amount to convert"
        />
      </div>
    </div>
  );
};
