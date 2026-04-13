import React, { useRef, useEffect } from 'react';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';
import WelcomeScreen from './WelcomeScreen';

/**
 * Main chat area component.
 * Renders the message list (or welcome screen) and the pinned input bar.
 *
 * @param {{
 *   messages: Array,
 *   onSend: (text: string) => void,
 *   isLoading: boolean
 * }} props
 */
export default function ChatWindow({ messages, onSend, isLoading }) {
  const bottomRef = useRef(null);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom whenever messages change
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  return (
    <div className="chat-container flex-1 flex flex-col overflow-hidden">
      {/* Message list area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-4 chat-scroll"
      >
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestionClick={onSend} />
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </>
        )}
        {/* Invisible anchor for auto-scroll */}
        <div ref={bottomRef} />
      </div>

      {/* Pinned input bar */}
      <InputBar onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
