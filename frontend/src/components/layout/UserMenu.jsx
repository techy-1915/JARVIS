import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export default function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  // Close on outside click and Escape key
  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    function handleKeyDown(e) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  const displayName = user?.username || user?.email || 'User';
  const email = user?.email || '';
  const initial = displayName.charAt(0).toUpperCase();

  return (
    <div className="relative" ref={menuRef}>
      {/* Avatar button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold text-sm transition-all hover:opacity-80 hover:scale-105 focus:outline-none"
        style={{ background: 'linear-gradient(135deg, #58a6ff, #a371f7)' }}
        title={displayName}
        aria-haspopup="true"
        aria-expanded={open}
      >
        {initial}
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="absolute right-0 mt-2 w-60 rounded-lg border border-[#30363d] bg-[#161b22] shadow-lg z-50"
          style={{ animation: 'fadeSlideDown 0.15s ease-out' }}
        >
          {/* User info */}
          <div className="px-4 py-3 flex items-center gap-3 border-b border-[#30363d]">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-base shrink-0"
              style={{ background: 'linear-gradient(135deg, #58a6ff, #a371f7)' }}
            >
              {initial}
            </div>
            <div className="min-w-0">
              <p className="text-[#e6edf3] font-semibold text-sm truncate">{displayName}</p>
              {email && (
                <p className="text-[#8b949e] text-xs truncate">{email}</p>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="py-1">
            <button
              onClick={async () => {
                setOpen(false);
                await logout();
              }}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-[#e6edf3] hover:text-red-400 hover:bg-[#21262d] transition-colors text-left"
            >
              {/* Logout icon */}
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path fillRule="evenodd" d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0v2z"/>
                <path fillRule="evenodd" d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3z"/>
              </svg>
              Log out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
