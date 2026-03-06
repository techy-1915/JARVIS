import React from 'react';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export default function ChatWindow({ messages, isTyping, onSend, error }) {
  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} isTyping={isTyping} />
      {error && (
        <div className="mx-4 mb-2 px-3 py-2 rounded-lg bg-[#f85149]/10 border border-[#f85149]/30 text-[#f85149] text-sm">
          {error}
        </div>
      )}
      <ChatInput onSend={onSend} disabled={isTyping} />
    </div>
  );
}
