import React from 'react';
import { ShoppingCart } from 'lucide-react';

const SUGGESTIONS = [
  'How long does shipping take?',
  "What's your return policy?",
  'How do I reset my password?',
  'What payment methods do you accept?',
];

/**
 * Welcome screen displayed when the chat is empty.
 * Shows brand identity and clickable suggestion chips.
 *
 * @param {{ onSuggestionClick: (text: string) => void }} props
 */
export default function WelcomeScreen({ onSuggestionClick }) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-12 text-center select-none">
      {/* Logo */}
      <div className="w-16 h-16 rounded-2xl bg-primary-600 flex items-center justify-center shadow-lg mb-5">
        <ShoppingCart size={32} className="text-white" />
      </div>

      {/* Heading */}
      <h1 className="text-2xl font-bold text-surface-800 mb-2">
        Hi! I'm NexaCart's AI Support Assistant
      </h1>
      <p className="text-surface-500 text-sm max-w-sm mb-8 leading-relaxed">
        Ask me anything about shipping, returns, exchanges, payments, or your
        account.
      </p>

      {/* Suggestion chips */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-md">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onSuggestionClick(suggestion)}
            className="text-left px-4 py-3 rounded-xl border border-surface-200 bg-white hover:border-primary-400 hover:bg-primary-50 text-sm text-surface-700 font-medium transition-all shadow-sm hover:shadow active:scale-[0.98]"
          >
            {suggestion}
          </button>
        ))}
      </div>

      <p className="text-xs text-surface-400 mt-8">
        Powered by NexaCart AI · Responses are based on our knowledge base
      </p>
    </div>
  );
}
