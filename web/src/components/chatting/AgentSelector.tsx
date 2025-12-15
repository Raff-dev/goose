import type { AgentSummary } from "../../api/types";

interface AgentSelectorProps {
  agents: AgentSummary[];
  selectedAgentId: string;
  onAgentChange: (agentId: string) => void;
}

export function AgentSelector({
  agents,
  selectedAgentId,
  onAgentChange,
}: AgentSelectorProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        Agent
      </label>
      <select
        value={selectedAgentId}
        onChange={(e) => onAgentChange(e.target.value)}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {agents.map((agent) => (
          <option key={agent.id} value={agent.id}>
            {agent.name}
          </option>
        ))}
      </select>
    </div>
  );
}
