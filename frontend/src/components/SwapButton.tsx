import React from 'react';
import { ArrowLeftRight } from 'lucide-react';

interface SwapButtonProps {
  onSwap: () => void;
  disabled?: boolean;
}

export const SwapButton: React.FC<SwapButtonProps> = ({ onSwap, disabled = false }) => {
  return (
    <div className="swap-button-wrapper">
      <button
        type="button"
        className="swap-btn"
        onClick={onSwap}
        disabled={disabled}
        aria-label="Swap source and target currencies"
        title="Swap currencies"
      >
        <ArrowLeftRight size={17} strokeWidth={2} />
      </button>
    </div>
  );
};
