import type { ToolSummary } from '../../api/types';
import { ToolCard } from './ToolCard';

interface ToolListProps {
  tools: ToolSummary[];
  selectedTool: string | null;
  onSelectTool: (name: string) => void;
}

export function ToolList({ tools, selectedTool, onSelectTool }: ToolListProps) {
  return (
    <div className="space-y-2">
      {tools.map(tool => (
        <ToolCard
          key={tool.name}
          tool={tool}
          isSelected={selectedTool === tool.name}
          onClick={() => onSelectTool(tool.name)}
        />
      ))}
    </div>
  );
}
