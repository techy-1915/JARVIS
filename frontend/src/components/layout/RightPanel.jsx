import React from 'react';
import EventLog from '../events/EventLog';

export default function RightPanel({ isOpen, logs }) {
  return (
    <aside
      className="flex flex-col bg-[#161b22] border-l border-[#30363d] sidebar-transition overflow-hidden shrink-0"
      style={{ width: isOpen ? '280px' : '0px', opacity: isOpen ? 1 : 0 }}
    >
      <div className="w-[280px] flex flex-col h-full">
        <div className="px-4 py-3 border-b border-[#30363d] flex items-center gap-2">
          <span className="text-[#8b949e] text-xs font-semibold uppercase tracking-wider">Event Log</span>
        </div>
        <div className="flex-1 overflow-y-auto">
          <EventLog logs={logs} />
        </div>
      </div>
    </aside>
  );
}
