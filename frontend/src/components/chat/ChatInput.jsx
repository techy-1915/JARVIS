import React, { useState, useRef, useCallback } from 'react';

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');
  const textareaRef = useRef(null);

  const handleSend = useCallback(() => {
    if (disabled || !value.trim()) return;
    onSend(value.trim());
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [value, onSend, disabled]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e) => {
    setValue(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
    }
  };

  return (
    <div className="px-4 pb-4 pt-2 border-t border-[#30363d] bg-[#0d1117]">
      <div className="flex items-end gap-3 bg-[#161b22] border border-[#30363d] rounded-2xl px-4 py-3 focus-within:border-[#58a6ff] transition-colors">
        <textarea
          ref={textareaRef}
          value={value}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Message JARVIS... (Enter to send, Shift+Enter for new line)"
          rows={1}
          className="flex-1 bg-transparent text-[#e6edf3] text-sm resize-none outline-none placeholder-[#8b949e] leading-relaxed"
          style={{ maxHeight: '200px' }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !value.trim()}
          className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors disabled:opacity-40 disabled:cursor-not-allowed bg-[#58a6ff] hover:bg-[#79b8ff] text-[#0d1117]"
          title="Send message"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
            <path d="M15.854.146a.5.5 0 0 1 .11.54l-5.819 14.547a.75.75 0 0 1-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 0 1 .124-1.33L15.314.037a.5.5 0 0 1 .54.11ZM6.636 10.07l2.761 4.338L14.13 2.576 6.636 10.07Zm6.787-8.201L1.591 6.602l4.339 2.76 7.494-7.493Z"/>
          </svg>
        </button>
      </div>
      <p className="text-[#8b949e] text-xs text-center mt-2">
        JARVIS may make mistakes. Verify important information.
      </p>
    </div>
  );
}
