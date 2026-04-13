import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import clsx from 'clsx';

const MAX_CHARS = 500;

/**
 * Pinned input bar with an auto-expanding textarea and send button.
 *
 * @param {{ onSend: (text: string) => void, isLoading: boolean }} props
 */
export default function InputBar({ onSend, isLoading }) {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize the textarea up to ~5 lines
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    const lineHeight = 24;
    const maxHeight = lineHeight * 5 + 24; // 5 lines + padding
    ta.style.height = `${Math.min(ta.scrollHeight, maxHeight)}px`;
  }, [text]);

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleSend() {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setText('');
  }

  const remaining = MAX_CHARS - text.length;
  const nearLimit = remaining <= 60;
  const canSend = text.trim().length > 0 && !isLoading && text.length <= MAX_CHARS;

  return (
    <div className="border-t border-surface-200 bg-white px-4 py-3">
      <div
        className={clsx(
          'flex items-end gap-2 rounded-xl border px-3 py-2 transition-colors',
          isLoading
            ? 'border-surface-200 bg-surface-50'
            : 'border-surface-300 bg-white focus-within:border-primary-500 focus-within:ring-2 focus-within:ring-primary-100'
        )}
      >
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder="Ask about shipping, returns, payments…"
          rows={1}
          maxLength={MAX_CHARS}
          className="flex-1 resize-none bg-transparent text-sm text-surface-800 placeholder-surface-400 outline-none leading-6 disabled:opacity-50"
          style={{ minHeight: '24px' }}
        />

        <div className="flex items-center gap-2 flex-shrink-0 pb-0.5">
          {nearLimit && (
            <span
              className={clsx(
                'text-xs font-mono',
                remaining <= 0 ? 'text-danger-600' : 'text-warning-600'
              )}
            >
              {remaining}
            </span>
          )}

          <button
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Send message"
            className={clsx(
              'w-8 h-8 rounded-lg flex items-center justify-center transition-all',
              canSend
                ? 'bg-primary-600 text-white hover:bg-primary-700 active:scale-95'
                : 'bg-surface-200 text-surface-400 cursor-not-allowed'
            )}
          >
            <Send size={15} />
          </button>
        </div>
      </div>

      <p className="text-center text-xs text-surface-400 mt-2">
        Press <kbd className="font-mono bg-surface-100 px-1 rounded">Enter</kbd> to send ·{' '}
        <kbd className="font-mono bg-surface-100 px-1 rounded">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
