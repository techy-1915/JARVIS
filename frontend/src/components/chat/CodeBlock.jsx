import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import CopyButton from './CopyButton';

export default function CodeBlock({ language, code }) {
  return (
    <div className="relative group my-4">
      <div className="flex items-center justify-between bg-[#0d1117] border border-[#30363d] border-b-0 rounded-t-lg px-4 py-2">
        <span className="text-[#8b949e] text-xs font-mono">{language}</span>
        <CopyButton text={code} />
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: '0 0 8px 8px',
          borderTop: 'none',
          fontSize: '13px',
          lineHeight: '1.5',
        }}
        codeTagProps={{
          style: {
            fontFamily: "'Fira Code', 'Consolas', 'Monaco', monospace",
          },
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
