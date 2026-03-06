import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';

export default function MessageList({ messages, isTyping }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  if (!messages.length && !isTyping) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-center px-8">
        <div className="w-16 h-16 rounded-full bg-[#58a6ff] flex items-center justify-center text-[#0d1117] font-bold text-2xl mb-4">
          J
        </div>
        <h2 className="text-[#e6edf3] text-2xl font-semibold mb-2">How can I help?</h2>
        <p className="text-[#8b949e] text-sm max-w-sm">
          I'm JARVIS, your AI assistant. Ask me anything — I'm here to help.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      {isTyping && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
