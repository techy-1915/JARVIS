import React from 'react';
import { MODEL_NAME, APP_VERSION } from '../../config';
import SystemStatus from '../status/SystemStatus';

export default function NavigationBar({ wsStatus, apiStatus, onToggleSidebar, onToggleRightPanel }) {
  return (
    <header className="flex items-center justify-between px-4 h-14 border-b border-[#30363d] bg-[#161b22] shrink-0">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded hover:bg-[#30363d] text-[#8b949e] hover:text-[#e6edf3] transition-colors"
          title="Toggle sidebar"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
            <path d="M2 3h12a1 1 0 0 1 0 2H2a1 1 0 0 1 0-2zm0 4h12a1 1 0 0 1 0 2H2a1 1 0 0 1 0-2zm0 4h12a1 1 0 0 1 0 2H2a1 1 0 0 1 0-2z"/>
          </svg>
        </button>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-[#58a6ff] flex items-center justify-center text-[#0d1117] font-bold text-sm">J</div>
          <span className="font-semibold text-[#e6edf3] text-lg tracking-wide">JARVIS</span>
          <span className="text-[#8b949e] text-xs hidden sm:block">v{APP_VERSION}</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-[#8b949e] text-xs px-2 py-1 rounded bg-[#0d1117] border border-[#30363d] hidden sm:block">
          {MODEL_NAME}
        </span>
        <SystemStatus wsStatus={wsStatus} apiStatus={apiStatus} />
        <button
          onClick={onToggleRightPanel}
          className="p-1.5 rounded hover:bg-[#30363d] text-[#8b949e] hover:text-[#e6edf3] transition-colors"
          title="Toggle event log"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
            <path d="M1 2.5A1.5 1.5 0 0 1 2.5 1h11A1.5 1.5 0 0 1 15 2.5v11a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 13.5v-11zm1.5-.5a.5.5 0 0 0-.5.5v11a.5.5 0 0 0 .5.5H10V2H2.5zm9 0v12h1a.5.5 0 0 0 .5-.5v-11a.5.5 0 0 0-.5-.5h-1z"/>
          </svg>
        </button>
      </div>
    </header>
  );
}
