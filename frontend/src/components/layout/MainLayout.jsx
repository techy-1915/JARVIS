import React from 'react';
import NavigationBar from './NavigationBar';
import Sidebar from './Sidebar';
import RightPanel from './RightPanel';

export default function MainLayout({ children, wsStatus, apiStatus, sidebarOpen, rightPanelOpen, onToggleSidebar, onToggleRightPanel, conversations, activeId, onSelectConv, onCreateConv, onRenameConv, onDeleteConv, logs }) {
  return (
    <div className="flex flex-col h-full bg-[#0d1117]">
      <NavigationBar
        wsStatus={wsStatus}
        apiStatus={apiStatus}
        onToggleSidebar={onToggleSidebar}
        onToggleRightPanel={onToggleRightPanel}
      />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          isOpen={sidebarOpen}
          conversations={conversations}
          activeId={activeId}
          onSelect={onSelectConv}
          onCreate={onCreateConv}
          onRename={onRenameConv}
          onDelete={onDeleteConv}
        />
        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
        <RightPanel isOpen={rightPanelOpen} logs={logs} />
      </div>
    </div>
  );
}
