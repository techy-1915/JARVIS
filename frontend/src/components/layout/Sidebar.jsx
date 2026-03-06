import React from 'react';
import NewChatButton from '../sidebar/NewChatButton';
import ConversationList from '../sidebar/ConversationList';

export default function Sidebar({ isOpen, conversations, activeId, onSelect, onCreate, onRename, onDelete }) {
  return (
    <aside
      className="flex flex-col bg-[#161b22] border-r border-[#30363d] sidebar-transition overflow-hidden shrink-0"
      style={{ width: isOpen ? '260px' : '0px', opacity: isOpen ? 1 : 0 }}
    >
      <div className="w-[260px] flex flex-col h-full">
        <div className="p-3 border-b border-[#30363d]">
          <NewChatButton onClick={onCreate} />
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          <ConversationList
            conversations={conversations}
            activeId={activeId}
            onSelect={onSelect}
            onRename={onRename}
            onDelete={onDelete}
          />
        </div>
      </div>
    </aside>
  );
}
