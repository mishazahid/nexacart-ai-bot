import React, { useState, useEffect, useCallback } from 'react';
import { ShoppingCart, Trash2, Wifi, WifiOff } from 'lucide-react';
import clsx from 'clsx';
import ChatWindow from './components/ChatWindow';
import { useChat } from './hooks/useChat';
import { checkHealth } from './api/chat';

/**
 * Root application component.
 *
 * Renders the header (logo, status indicator, clear button), the chat window,
 * and an auto-dismissing error toast.
 */
export default function App() {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();
  const [isOnline, setIsOnline] = useState(null); // null = checking
  const [toastVisible, setToastVisible] = useState(false);

  // Health check on mount and every 30 seconds
  useEffect(() => {
    const check = () => checkHealth().then((data) => setIsOnline(data.status === 'ok'));
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  // Show toast when error appears
  useEffect(() => {
    if (error) {
      setToastVisible(true);
      const timer = setTimeout(() => setToastVisible(false), 4000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const handleSend = useCallback(
    (text) => {
      sendMessage(text);
    },
    [sendMessage]
  );

  return (
    <div className="h-screen flex flex-col bg-surface-50 min-w-[320px]">
      {/* ---- Header ---- */}
      <header className="flex items-center justify-between px-4 py-3 bg-white border-b border-surface-200 shadow-sm flex-shrink-0">
        {/* Logo + title */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
            <ShoppingCart size={18} className="text-white" />
          </div>
          <div className="leading-tight">
            <span className="font-bold text-surface-800 text-sm">NexaCart</span>
            <span className="text-primary-600 font-semibold text-sm"> AI Support</span>
          </div>
        </div>

        {/* Right side: status + clear button */}
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          <div className="flex items-center gap-1.5">
            {isOnline === null ? (
              <span className="w-2 h-2 rounded-full bg-surface-300 animate-pulse" />
            ) : isOnline ? (
              <>
                <span className="w-2 h-2 rounded-full bg-success-500" />
                <span className="text-xs text-surface-500 hidden sm:inline">Online</span>
                <Wifi size={13} className="text-success-500 hidden sm:inline" />
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-danger-500" />
                <span className="text-xs text-surface-500 hidden sm:inline">Offline</span>
                <WifiOff size={13} className="text-danger-500 hidden sm:inline" />
              </>
            )}
          </div>

          {/* Clear chat button — only shown when messages exist */}
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              title="Clear chat"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-surface-500 hover:text-danger-600 hover:bg-danger-50 border border-transparent hover:border-danger-200 transition-all"
            >
              <Trash2 size={13} />
              <span className="hidden sm:inline">Clear</span>
            </button>
          )}
        </div>
      </header>

      {/* ---- Main chat area ---- */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <ChatWindow
          messages={messages}
          onSend={handleSend}
          isLoading={isLoading}
        />
      </main>

      {/* ---- Error toast ---- */}
      {toastVisible && error && (
        <div
          className={clsx(
            'fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-xl shadow-lg',
            'bg-danger-600 text-white text-sm font-medium max-w-sm w-full mx-4',
            'flex items-center gap-2',
            'animate-toast-in'
          )}
          role="alert"
        >
          <svg
            className="w-4 h-4 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
              clipRule="evenodd"
            />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}
