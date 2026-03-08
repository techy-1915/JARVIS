import React, { useEffect, useRef } from 'react';

const LEVEL_STYLES = {
  success: 'text-green-400',
  error: 'text-red-400',
  warning: 'text-yellow-400',
  info: 'text-blue-400',
};

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export default function EventLog({ logs = [] }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[#8b949e] text-xs py-8">
        No events yet
      </div>
    );
  }

  return (
    <div className="p-3 space-y-1">
      {logs.map((log, i) => (
        <div key={i} className="flex gap-2 text-xs font-mono">
          <span className="text-[#484f58] shrink-0">{formatTime(log.timestamp)}</span>
          <span className={LEVEL_STYLES[log.level] || 'text-[#8b949e]'}>{log.message}</span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
