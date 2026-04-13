import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { sendMessage as apiSendMessage } from '../api/chat';

const STORAGE_KEY = 'nexacart_session_id';

function getOrCreateSessionId() {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) return stored;
  const fresh = uuidv4();
  localStorage.setItem(STORAGE_KEY, fresh);
  return fresh;
}

/**
 * Custom hook that manages the full chat state for NexaCart AI Support.
 *
 * @returns {{
 *   messages: Array,
 *   isLoading: boolean,
 *   error: string|null,
 *   sessionId: string,
 *   sendMessage: (query: string) => Promise<void>,
 *   clearChat: () => void,
 * }}
 */
export function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(getOrCreateSessionId);

  const sendMessage = useCallback(
    async (query) => {
      if (!query.trim() || isLoading) return;

      const userMessageId = uuidv4();
      const loadingMessageId = uuidv4();

      // Immediately add the user message
      setMessages((prev) => [
        ...prev,
        {
          id: userMessageId,
          role: 'user',
          content: query.trim(),
          timestamp: new Date(),
          confidence: null,
          sources: [],
          isLoading: false,
          isFallback: false,
        },
      ]);

      // Add a placeholder loading assistant message
      setMessages((prev) => [
        ...prev,
        {
          id: loadingMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          confidence: null,
          sources: [],
          isLoading: true,
          isFallback: false,
        },
      ]);

      setIsLoading(true);
      setError(null);

      try {
        // Build history from last 6 non-loading messages for context
        const history = messages
          .filter((m) => !m.isLoading && m.content)
          .slice(-6)
          .map((m) => ({ role: m.role, content: m.content }));

        const data = await apiSendMessage(query.trim(), sessionId, history);

        // Replace the loading placeholder with the real response
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === loadingMessageId
              ? {
                  id: loadingMessageId,
                  role: 'assistant',
                  content: data.answer,
                  timestamp: new Date(),
                  confidence: data.confidence_score,
                  sources: data.sources || [],
                  isLoading: false,
                  isFallback: data.is_fallback || false,
                }
              : msg
          )
        );
      } catch (err) {
        const errorText =
          err.message || 'Something went wrong. Please try again.';
        setError(errorText);

        // Replace the loading placeholder with an error message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === loadingMessageId
              ? {
                  id: loadingMessageId,
                  role: 'assistant',
                  content:
                    'Sorry, I encountered an error. Please try again or contact support@nexacart.com.',
                  timestamp: new Date(),
                  confidence: 0,
                  sources: [],
                  isLoading: false,
                  isFallback: true,
                }
              : msg
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, sessionId]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    const newSession = uuidv4();
    setSessionId(newSession);
    localStorage.setItem(STORAGE_KEY, newSession);
  }, []);

  return { messages, isLoading, error, sessionId, sendMessage, clearChat };
}
