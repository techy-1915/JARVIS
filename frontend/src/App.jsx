import React, { useState, useEffect, useCallback } from 'react';
import MainLayout from './components/layout/MainLayout';
import ChatWindow from './components/chat/ChatWindow';
import { useWebSocket } from './hooks/useWebSocket';
import { useConversations } from './hooks/useConversations';
import { useChat } from './hooks/useChat';
import { getStatus } from './services/api';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(false);
  const [logs, setLogs] = useState([]);
  const [apiStatus, setApiStatus] = useState('checking');

  const addLog = useCallback((log) => {
    setLogs((prev) => [...prev.slice(-199), log]);
  }, []);

  const { status: wsStatus } = useWebSocket(
    useCallback((data) => {
      addLog({ level: 'info', message: `WS: ${data}`, timestamp: Date.now() });
    }, [addLog])
  );

  const {
    conversations, activeId, activeConversation,
    setActiveId, createConversation, getOrCreateActive,
    addMessage, renameConversation, deleteConversation,
  } = useConversations();

  const { isTyping, error, send } = useChat({
    activeId,
    getOrCreateActive,
    addMessage,
    addLog,
  });

  useEffect(() => {
    const check = async () => {
      try {
        await getStatus();
        setApiStatus('ok');
        addLog({ level: 'success', message: 'API connection established', timestamp: Date.now() });
      } catch {
        setApiStatus('error');
        addLog({ level: 'error', message: 'API connection failed', timestamp: Date.now() });
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, [addLog]);

  const handleSelectConv = useCallback((id) => {
    setActiveId(id);
  }, [setActiveId]);

  const messages = activeConversation?.messages || [];

  return (
    <MainLayout
      wsStatus={wsStatus}
      apiStatus={apiStatus}
      sidebarOpen={sidebarOpen}
      rightPanelOpen={rightPanelOpen}
      onToggleSidebar={() => setSidebarOpen((v) => !v)}
      onToggleRightPanel={() => setRightPanelOpen((v) => !v)}
      conversations={conversations}
      activeId={activeId}
      onSelectConv={handleSelectConv}
      onCreateConv={createConversation}
      onRenameConv={renameConversation}
      onDeleteConv={deleteConversation}
      logs={logs}
    >
      <ChatWindow
        messages={messages}
        isTyping={isTyping}
        onSend={send}
        error={error}
      />
    </MainLayout>
  );
}
