import { useCallback, useRef, useState } from 'react';
import api, { getErrorMessage } from '../services/api';

/**
 * The chat transcript. Lives in App so the conversation survives switching views.
 * Assistant messages carry `status: 'blocked' | 'error'` when there is no answer;
 * those are left out of the history sent back to the backend.
 */
export default function useConversation({ onSettled } = {}) {
  const [messages, setMessagesState] = useState([]);
  const [pending, setPending] = useState(false);
  const messagesRef = useRef(messages);
  const activeRequest = useRef(null);
  const nextId = useRef(0);

  const setMessages = useCallback((updater) => {
    messagesRef.current = typeof updater === 'function' ? updater(messagesRef.current) : updater;
    setMessagesState(messagesRef.current);
  }, []);

  const ask = useCallback(
    async (text) => {
      const question = text.trim();
      if (!question || activeRequest.current) return false;

      const request = {};
      activeRequest.current = request;
      const history = messagesRef.current
        .filter((message) => !message.status)
        .map(({ role, content }) => ({ role, content }));
      setMessages((list) => [...list, { id: (nextId.current += 1), role: 'user', content: question }]);
      setPending(true);

      let reply;
      try {
        const { data } = await api.post('/api/query', { question, conversation_history: history });
        reply = {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          warnings: data.security_warnings || [],
        };
      } catch (error) {
        // The backend answers 400 only when the injection filter blocks a question.
        reply =
          error.response?.status === 400
            ? { role: 'assistant', status: 'blocked', content: '' }
            : { role: 'assistant', status: 'error', content: getErrorMessage(error, 'The request failed.') };
      }

      // Ignore replies to a conversation that was cleared while waiting.
      if (activeRequest.current === request) {
        activeRequest.current = null;
        setPending(false);
        setMessages((list) => [...list, { id: (nextId.current += 1), ...reply }]);
      }
      onSettled?.();
      return true;
    },
    [onSettled, setMessages]
  );

  const reset = useCallback(() => {
    activeRequest.current = null;
    setPending(false);
    setMessages([]);
  }, [setMessages]);

  /** Drop a failed exchange and ask the same question again. */
  const retry = useCallback(
    (replyId) => {
      if (activeRequest.current) return;
      const list = messagesRef.current;
      const index = list.findIndex((message) => message.id === replyId);
      const question = list[index - 1];
      if (index < 1 || question.role !== 'user') return;
      setMessages(list.filter((_, i) => i !== index && i !== index - 1));
      ask(question.content);
    },
    [ask, setMessages]
  );

  return { messages, pending, ask, reset, retry };
}
