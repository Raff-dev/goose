import { useCallback, useEffect, useState } from "react";
import { chattingApi } from "../api/chatting";
import type { AgentSummary, ConversationSummary } from "../api/types";
import {
    AgentSelector,
    ChatPanel,
    ConversationList,
} from "../components/chatting";
import { useGlobalError } from "../context/GlobalErrorContext";
import { getErrorMessage } from "../utils/errors";

export function ChattingView() {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedAgentId, setSelectedAgentId] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const { setError } = useGlobalError();

  // Fetch agents and conversations on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [agentsData, conversationsData] = await Promise.all([
          chattingApi.listAgents(),
          chattingApi.listConversations(),
        ]);
        setAgents(agentsData);
        setConversations(conversationsData);
        // Set default selections
        if (agentsData.length > 0) {
          setSelectedAgentId(agentsData[0].id);
          if (agentsData[0].models.length > 0) {
            setSelectedModel(agentsData[0].models[0]);
          }
        }
        setError(null);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    void fetchData();
  }, [setError]);

  const handleDeleteConversation = useCallback(
    async (id: string) => {
      try {
        await chattingApi.deleteConversation(id);
        setConversations((prev) => prev.filter((c) => c.id !== id));
        if (selectedConversationId === id) {
          setSelectedConversationId(null);
        }
      } catch (err) {
        setError(getErrorMessage(err));
      }
    },
    [selectedConversationId, setError]
  );

  const handleOpenNewChat = useCallback(async () => {
    if (agents.length === 0) {
      setError("No agents configured. Add agents to your GooseApp configuration.");
      return;
    }

    // Create conversation immediately
    try {
      const conversation = await chattingApi.createConversation({
        agent_id: selectedAgentId,
        model: selectedModel,
      });
      // Add to list and select it
      const conversationsData = await chattingApi.listConversations();
      setConversations(conversationsData);
      setSelectedConversationId(conversation.id);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, [agents.length, selectedAgentId, selectedModel, setError]);

  const handleSelectConversation = useCallback((id: string | null) => {
    setSelectedConversationId(id);
  }, []);

  const handlePanelError = useCallback(
    (message: string) => {
      setError(message);
    },
    [setError]
  );

  // Callback when conversation title updates (e.g., after first message)
  const handleConversationUpdate = useCallback(async () => {
    try {
      const conversationsData = await chattingApi.listConversations();
      setConversations(conversationsData);
    } catch {
      // Ignore - not critical
    }
  }, []);

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (agents.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-medium text-yellow-800 mb-2">No Agents Configured</h3>
        <p className="text-yellow-700">
          Add agents to your GooseApp configuration to start chatting:
        </p>
        <pre className="mt-4 bg-yellow-100 rounded p-3 text-left text-sm overflow-x-auto">
{`from goose import GooseApp
from example_system.agent import get_agent

app = GooseApp(
    agents=[
        {
            "name": "My Agent",
            "get_agent": get_agent,
            "models": ["gpt-4o-mini", "gpt-4o"],
        },
    ],
)`}
        </pre>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900">Chat</h2>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left sidebar: Agent selector + Conversation List */}
        <div className="lg:col-span-1 space-y-4">
          <AgentSelector
            agents={agents}
            selectedAgentId={selectedAgentId}
            selectedModel={selectedModel}
            onAgentChange={setSelectedAgentId}
            onModelChange={setSelectedModel}
          />
          <ConversationList
            conversations={conversations}
            selectedId={selectedConversationId}
            onSelect={handleSelectConversation}
            onDelete={handleDeleteConversation}
            onCreateNew={handleOpenNewChat}
          />
        </div>

        {/* Chat Panel */}
        <div className="lg:col-span-3">
          {selectedConversationId ? (
            <ChatPanel
              conversationId={selectedConversationId}
              onError={handlePanelError}
              onConversationUpdate={handleConversationUpdate}
            />
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg flex items-center justify-center h-[600px]">
              <div className="text-center text-gray-500">
                <p>Select a conversation or click "New" to start chatting.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
