import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { sendMessage } from '../services/api';

export function useChat({ getOrCreateActive, addMessage, addLog }) {
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState(null);

  const send = useCallback(async (text) => {
    if (!text.trim()) return;
    setError(null);

    const convId = getOrCreateActive();
    const userMsg = { id: uuidv4(), role: 'user', content: text, timestamp: Date.now() };
    addMessage(convId, userMsg);
    addLog?.({ level: 'info', message: `Sending message to JARVIS`, timestamp: Date.now() });

    setIsTyping(true);
    try {
      const data = await sendMessage(text, convId);
      
      // Handle different response formats from the backend
      let responseText;
      if (typeof data === 'string') {
        responseText = data;
      } else if (data.response) {
        responseText = data.response;
      } else if (data.result?.response) {
        responseText = data.result.response;
      } else {
        // If we still get raw JSON, stringify it (fallback)
        responseText = JSON.stringify(data, null, 2);
      }
      
      const assistantMsg = { id: uuidv4(), role: 'assistant', content: responseText, timestamp: Date.now() };
      addMessage(convId, assistantMsg);
      addLog?.({ level: 'success', message: `Response received`, timestamp: Date.now() });
    } catch (err) {
      setError(err.message);
      addLog?.({ level: 'error', message: `Error: ${err.message}`, timestamp: Date.now() });
    } finally {
      setIsTyping(false);
    }
  }, [getOrCreateActive, addMessage, addLog]);

  return { isTyping, error, send };
}