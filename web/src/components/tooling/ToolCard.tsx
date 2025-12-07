import type { ToolSummary } from '../../api/types';

interface ToolCardProps {
  tool: ToolSummary;
  isSelected: boolean;
  onClick: () => void;
}

export function ToolCard({ tool, isSelected, onClick }: ToolCardProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left p-3 rounded-lg border transition-colors ${
        isSelected
          ? 'bg-blue-50 border-blue-300'
          : 'bg-white border-gray-200 hover:bg-gray-50'
      }`}
    >
      <div className="font-medium text-gray-900">{tool.name}</div>
      <div className="text-sm text-gray-500 truncate">{tool.description}</div>
      <div className="text-xs text-gray-400 mt-1">
        {tool.parameter_count} parameter{tool.parameter_count !== 1 ? 's' : ''}
      </div>
    </button>
  );
}
