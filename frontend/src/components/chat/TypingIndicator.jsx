import React from 'react';

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 px-4 py-3">
      <div className="w-8 h-8 rounded-full bg-[#58a6ff] flex items-center justify-center text-[#0d1117] font-bold text-sm shrink-0">
        J
      </div>
      <div className="flex items-center gap-1 bg-[#161b22] border border-[#30363d] rounded-2xl rounded-tl-none px-4 py-3">
        <span className="typing-dot w-2 h-2 rounded-full bg-[#8b949e] block" />
        <span className="typing-dot w-2 h-2 rounded-full bg-[#8b949e] block" />
        <span className="typing-dot w-2 h-2 rounded-full bg-[#8b949e] block" />
      </div>
    </div>
  );
}
