import React from 'react';
import { Bot } from 'lucide-react';

/**
 * Animated three-dot typing indicator shown while the assistant is processing.
 */
export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-2 message-enter">
      {/* Bot avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-600 flex items-center justify-center shadow-sm">
        <Bot size={16} className="text-white" />
      </div>

      {/* Bubble */}
      <div className="bg-white border border-surface-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm max-w-xs">
        <div className="flex items-center gap-1.5 h-5">
          <span
            className="w-2 h-2 rounded-full bg-surface-400 inline-block"
            style={{ animation: 'bounceDot 1.2s 0s infinite ease-in-out' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-surface-400 inline-block"
            style={{ animation: 'bounceDot 1.2s 0.2s infinite ease-in-out' }}
          />
          <span
            className="w-2 h-2 rounded-full bg-surface-400 inline-block"
            style={{ animation: 'bounceDot 1.2s 0.4s infinite ease-in-out' }}
          />
        </div>
      </div>
    </div>
  );
}
