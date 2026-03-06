import React from 'react';

function Dot({ color, title }) {
  const colors = {
    green: 'bg-[#3fb950]',
    red: 'bg-[#f85149]',
    yellow: 'bg-yellow-400',
    gray: 'bg-[#8b949e]',
  };
  return (
    <span title={title} className={`inline-block w-2 h-2 rounded-full ${colors[color] || colors.gray}`} />
  );
}

export default function SystemStatus({ wsStatus, apiStatus }) {
  const wsColor = wsStatus === 'connected' ? 'green' : wsStatus === 'connecting' ? 'yellow' : 'red';
  const apiColor = apiStatus === 'ok' ? 'green' : apiStatus === 'checking' ? 'yellow' : 'red';

  return (
    <div className="flex items-center gap-3 text-xs text-[#8b949e]">
      <div className="flex items-center gap-1.5">
        <Dot color={apiColor} title={`API: ${apiStatus}`} />
        <span className="hidden sm:block">API</span>
      </div>
      <div className="flex items-center gap-1.5">
        <Dot color={wsColor} title={`WS: ${wsStatus}`} />
        <span className="hidden sm:block">WS</span>
      </div>
    </div>
  );
}
