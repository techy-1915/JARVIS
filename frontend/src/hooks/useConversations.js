import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { loadConversations, saveConversations } from '../services/storage';
import { truncate } from '../utils/formatters';

export function useConversations() {
  const [conversations, setConversations] = useState(() => loadConversations());
  const [activeId, setActiveId] = useState(null);

  const persist = useCallback((convs) => {
    setConversations(convs);
    saveConversations(convs);
  }, []);

  const createConversation = useCallback(() => {
    const id = uuidv4();
    const conv = { id, title: 'New Chat', messages: [], createdAt: Date.now(), updatedAt: Date.now() };
    persist([conv, ...conversations]);
    setActiveId(id);
    return id;
  }, [conversations, persist]);

  const getOrCreateActive = useCallback(() => {
    if (activeId) return activeId;
    return createConversation();
  }, [activeId, createConversation]);

  const addMessage = useCallback((convId, message) => {
    setConversations((prev) => {
      const updated = prev.map((c) => {
        if (c.id !== convId) return c;
        const msgs = [...c.messages, message];
        const title = c.title === 'New Chat' && message.role === 'user'
          ? truncate(message.content)
          : c.title;
        return { ...c, messages: msgs, title, updatedAt: Date.now() };
      });
      saveConversations(updated);
      return updated;
    });
  }, []);

  const renameConversation = useCallback((id, title) => {
    setConversations((prev) => {
      const updated = prev.map((c) => c.id === id ? { ...c, title } : c);
      saveConversations(updated);
      return updated;
    });
  }, []);

  const deleteConversation = useCallback((id) => {
    setConversations((prev) => {
      const updated = prev.filter((c) => c.id !== id);
      saveConversations(updated);
      return updated;
    });
    if (activeId === id) setActiveId(null);
  }, [activeId]);

  const activeConversation = conversations.find((c) => c.id === activeId) || null;

  return {
    conversations,
    activeId,
    activeConversation,
    setActiveId,
    createConversation,
    getOrCreateActive,
    addMessage,
    renameConversation,
    deleteConversation,
  };
}
