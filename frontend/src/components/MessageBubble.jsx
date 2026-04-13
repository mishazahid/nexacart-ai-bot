import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Bot, User, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import TypingIndicator from './TypingIndicator';
import ConfidenceBadge from './ConfidenceBadge';
import SourceCard from './SourceCard';
import { formatTimestamp } from '../utils/helpers';

/**
 * Renders a single chat message bubble for either the user or the assistant.
 *
 * @param {{ message: {
 *   role: 'user'|'assistant',
 *   content: string,
 *   timestamp: Date,
 *   confidence: number|null,
 *   sources: Array,
 *   isLoading: boolean,
 *   isFallback: boolean
 * }}} props
 */
export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (message.isLoading) {
    return <TypingIndicator />;
  }

  return (
    <div
      className={clsx(
        'flex items-start gap-2 message-enter',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm',
          isUser ? 'bg-surface-600' : 'bg-primary-600'
        )}
      >
        {isUser ? (
          <User size={16} className="text-white" />
        ) : (
          <Bot size={16} className="text-white" />
        )}
      </div>

      {/* Bubble content */}
      <div
        className={clsx(
          'flex flex-col gap-1.5 max-w-[78%]',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={clsx(
            'px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm',
            isUser
              ? 'bg-primary-600 text-white rounded-tr-sm'
              : clsx(
                  'bg-white text-surface-800 rounded-tl-sm border',
                  message.isFallback
                    ? 'border-warning-300 bg-warning-50'
                    : 'border-surface-200'
                )
          )}
        >
          {/* Fallback warning icon */}
          {!isUser && message.isFallback && (
            <div className="flex items-center gap-1.5 text-warning-600 text-xs font-medium mb-2">
              <AlertTriangle size={13} />
              <span>Escalated to human support</span>
            </div>
          )}

          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Confidence badge for assistant messages */}
        {!isUser && message.confidence !== null && (
          <ConfidenceBadge
            score={message.confidence}
            isFallback={message.isFallback}
          />
        )}

        {/* Source cards */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="w-full space-y-1">
            <p className="text-xs text-surface-400 font-medium px-0.5">
              Sources
            </p>
            {message.sources.map((source, idx) => (
              <SourceCard key={`${source.filename}-${idx}`} source={source} />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-surface-400 px-0.5">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
