import type { AgentSummary } from "../../api/types";

interface AgentSelectorProps {
  agents: AgentSummary[];
  selectedAgentId: string;
  selectedModel: string;
  onAgentChange: (agentId: string) => void;
  onModelChange: (model: string) => void;
}

export function AgentSelector({
  agents,
  selectedAgentId,
  selectedModel,
  onAgentChange,
  onModelChange,
}: AgentSelectorProps) {
  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  const handleAgentChange = (agentId: string) => {
    onAgentChange(agentId);
    const agent = agents.find((a) => a.id === agentId);
    if (agent && agent.models.length > 0 && !agent.models.includes(selectedModel)) {
      onModelChange(agent.models[0]);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Agent
        </label>
        <select
          value={selectedAgentId}
          onChange={(e) => handleAgentChange(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Model
        </label>
        <select
          value={selectedModel}
          onChange={(e) => onModelChange(e.target.value)}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {selectedAgent?.models.map((model) => (
            <option key={model} value={model}>
              {model}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
