import { PlusIcon, TrashIcon } from "@radix-ui/react-icons";
import type { ConversationSummary } from "../../api/types";

interface ConversationListProps {
  conversations: ConversationSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onCreateNew: () => void;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function ConversationList({
  conversations,
  selectedId,
  onSelect,
  onDelete,
  onCreateNew,
}: ConversationListProps) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Conversations</h3>
        <button
          onClick={onCreateNew}
          className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-white bg-blue-500 rounded-md hover:bg-blue-600 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          New
        </button>
      </div>

      <div className="divide-y divide-gray-100 max-h-[500px] overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-6 text-center text-gray-500 text-sm">
            No conversations yet. Click "New" to start chatting.
          </div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`p-3 cursor-pointer transition-colors group ${
                selectedId === conv.id
                  ? "bg-blue-50 border-l-2 border-blue-500"
                  : "hover:bg-gray-50"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{conv.title}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {conv.agent_name}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {conv.message_count} messages · {formatDate(conv.updated_at)}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conv.id);
                  }}
                  className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Delete conversation"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
