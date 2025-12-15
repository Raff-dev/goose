import { useMemo, useState } from 'react';

import type { ToolSummary } from '../../api/types';
import { ToolCard } from './ToolCard';

interface ToolListProps {
  tools: ToolSummary[];
  selectedTool: string | null;
  onSelectTool: (name: string) => void;
}

export function ToolList({ tools, selectedTool, onSelectTool }: ToolListProps) {
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  const groupedByGroup = useMemo(() => {
    return tools.reduce((map, tool) => {
      const groupName = tool.group && tool.group.trim().length > 0 ? tool.group.trim() : 'Ungrouped';
      const existing = map.get(groupName) ?? [];
      existing.push(tool);
      map.set(groupName, existing);
      return map;
    }, new Map<string, ToolSummary[]>());
  }, [tools]);

  const toggleGroup = (groupName: string) => {
    setCollapsedGroups(prev => ({
      ...prev,
      [groupName]: !(prev[groupName] ?? false),
    }));
  };

  return (
    <div className="space-y-6">
      {[...groupedByGroup.entries()].map(([groupName, groupTools], index) => {
        const isCollapsed = collapsedGroups[groupName] ?? false;
        return (
          <div
            key={groupName}
            className={`pt-4 ${index === 0 ? 'border-t border-transparent' : 'border-t border-slate-200'} `}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 min-w-0">
                <h3 className="text-sm font-semibold text-slate-700 truncate">{groupName}</h3>
                <span className="text-xs text-slate-400">({groupTools.length})</span>
              </div>
              <button
                type="button"
                onClick={() => toggleGroup(groupName)}
                className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
                aria-label={`${isCollapsed ? 'Expand' : 'Collapse'} ${groupName}`}
              >
                <svg
                  className="w-3.5 h-3.5 text-slate-500"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  {isCollapsed ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 9l7 7 7-7" />
                  )}
                </svg>
                {isCollapsed ? 'Expand' : 'Collapse'}
              </button>
            </div>
            <div
              className={`overflow-hidden transition-[max-height,opacity] duration-200 ease-out ${
                isCollapsed ? 'max-h-0 opacity-0' : 'max-h-[2000px] opacity-100'
              }`}
              aria-hidden={isCollapsed}
            >
              <div className="space-y-2">
                {groupTools.map(tool => (
                  <ToolCard
                    key={tool.name}
                    tool={tool}
                    isSelected={selectedTool === tool.name}
                    onClick={() => onSelectTool(tool.name)}
                  />
                ))}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
