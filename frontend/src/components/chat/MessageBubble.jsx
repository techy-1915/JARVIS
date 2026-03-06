import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { formatTimestamp } from '../../utils/formatters';

function CodeBlock({ children, className }) {
  const match = /language-(\w+)/.exec(className || '');
  return match ? (
    <SyntaxHighlighter
      style={oneDark}
      language={match[1]}
      PreTag="div"
      customStyle={{ borderRadius: '8px', fontSize: '13px', margin: '8px 0' }}
    >
      {String(children).replace(/\n$/, '')}
    </SyntaxHighlighter>
  ) : (
    <code className="bg-[#0d1117] text-[#e6edf3] px-1.5 py-0.5 rounded text-sm font-mono">
      {children}
    </code>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-2">
        <div className="max-w-[75%]">
          <div className="bg-[#58a6ff] text-[#0d1117] px-4 py-2.5 rounded-2xl rounded-tr-none text-sm leading-relaxed whitespace-pre-wrap break-words">
            {message.content}
          </div>
          <p className="text-[#8b949e] text-xs mt-1 text-right">{formatTimestamp(message.timestamp)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 px-4 py-2">
      <div className="w-8 h-8 rounded-full bg-[#58a6ff] flex items-center justify-center text-[#0d1117] font-bold text-sm shrink-0 mt-0.5">
        J
      </div>
      <div className="max-w-[75%]">
        <div className="bg-[#161b22] border border-[#30363d] text-[#e6edf3] px-4 py-3 rounded-2xl rounded-tl-none text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code: CodeBlock,
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#58a6ff] hover:underline">
                  {children}
                </a>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        <p className="text-[#8b949e] text-xs mt-1">{formatTimestamp(message.timestamp)}</p>
      </div>
    </div>
  );
}
