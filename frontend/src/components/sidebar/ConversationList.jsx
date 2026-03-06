import React from 'react';
import ConversationItem from './ConversationItem';
import { formatDate } from '../../utils/formatters';

function groupByDate(conversations) {
  const groups = {};
  conversations.forEach((c) => {
    const label = formatDate(c.updatedAt || c.createdAt);
    if (!groups[label]) groups[label] = [];
    groups[label].push(c);
  });
  return groups;
}

export default function ConversationList({ conversations, activeId, onSelect, onRename, onDelete }) {
  if (!conversations.length) {
    return (
      <div className="text-center text-[#8b949e] text-xs mt-8 px-4">
        No conversations yet.<br />Start a new chat!
      </div>
    );
  }

  const groups = groupByDate(conversations);

  return (
    <div className="flex flex-col gap-4">
      {Object.entries(groups).map(([label, convs]) => (
        <div key={label}>
          <p className="text-[#8b949e] text-xs px-3 mb-1 font-semibold uppercase tracking-wider">{label}</p>
          <div className="flex flex-col gap-0.5">
            {convs.map((c) => (
              <ConversationItem
                key={c.id}
                conv={c}
                isActive={c.id === activeId}
                onSelect={onSelect}
                onRename={onRename}
                onDelete={onDelete}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
