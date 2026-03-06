import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeBlock from './CodeBlock';
import CopyButton from './CopyButton';
import { formatTimestamp } from '../../utils/formatters';

function InlineCode({ children }) {
  return (
    <code className="bg-[#0d1117] text-[#e6edf3] px-1.5 py-0.5 rounded text-sm font-mono">
      {children}
    </code>
  );
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end px-4 py-2 group">
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
    <div className="flex items-start gap-3 px-4 py-2 group">
      <div className="w-8 h-8 rounded-full bg-[#58a6ff] flex items-center justify-center text-[#0d1117] font-bold text-sm shrink-0 mt-0.5">
        J
      </div>
      <div className="max-w-[75%] flex-1">
        <div className="relative">
          <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
            <CopyButton text={message.content} />
          </div>
          <div className="bg-[#161b22] border border-[#30363d] text-[#e6edf3] px-4 py-3 rounded-2xl rounded-tl-none text-sm leading-relaxed">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ inline, className, children }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <CodeBlock
                      language={match[1]}
                      code={String(children).replace(/\n$/, '')}
                    />
                  ) : (
                    <InlineCode>{children}</InlineCode>
                  );
                },
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-[#58a6ff] hover:underline"
                  >
                    {children}
                  </a>
                ),
                p: ({ children }) => (
                  <p className="mb-3 last:mb-0">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>
                ),
                h1: ({ children }) => (
                  <h1 className="text-xl font-bold mb-2 mt-4 first:mt-0">{children}</h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-base font-bold mb-2 mt-2 first:mt-0">{children}</h3>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-[#30363d] pl-4 my-3 text-[#8b949e]">
                    {children}
                  </blockquote>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
        <p className="text-[#8b949e] text-xs mt-1">{formatTimestamp(message.timestamp)}</p>
      </div>
    </div>
  );
}
