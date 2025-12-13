import { useCallback, useEffect, useRef, useState } from "react";
import { chattingApi } from "../../api/chatting";
import type { Conversation, Message, StreamEvent } from "../../api/types";
import LoadingDots from "../LoadingDots";
import { MessageCards } from "../MessageCards";
import { MessageInput } from "./MessageInput";

interface ChatPanelProps {
  conversationId: string;
  onError: (message: string) => void;
  onConversationUpdate?: () => void;
}

export function ChatPanel({ conversationId, onError, onConversationUpdate }: ChatPanelProps) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch conversation on mount or when ID changes
  useEffect(() => {
    let cancelled = false;

    const fetchConversation = async () => {
      setLoading(true);
      try {
        const data = await chattingApi.getConversation(conversationId);
        if (!cancelled) {
          setConversation(data);
        }
      } catch (err) {
        if (!cancelled) {
          onError("Failed to load conversation");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void fetchConversation();

    return () => {
      cancelled = true;
    };
  }, [conversationId, onError]);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages, streamingContent]);

  // Clean up WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const handleSendMessage = useCallback(
    (content: string) => {
      if (!conversation || streaming) return;

      // Close existing WebSocket if any
      if (wsRef.current) {
        wsRef.current.close();
      }

      setStreaming(true);
      setStreamingContent("");

      const wsUrl = chattingApi.getWebSocketUrl(conversationId);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      let accumulatedContent = "";
      const pendingMessages: Message[] = [];

      ws.onopen = () => {
        // Send the message
        ws.send(JSON.stringify({ type: "send_message", content }));
      };

      ws.onmessage = (event) => {
        try {
          const streamEvent: StreamEvent = JSON.parse(event.data);

          switch (streamEvent.type) {
            case "message":
              // Human message echoed back - add to conversation
              const humanMsg = streamEvent.data as unknown as Message;
              pendingMessages.push(humanMsg);
              setConversation((prev) =>
                prev
                  ? {
                      ...prev,
                      messages: [...prev.messages, humanMsg],
                    }
                  : prev
              );
              break;

            case "token":
              // Accumulate streaming content
              accumulatedContent += streamEvent.data.content as string;
              setStreamingContent(accumulatedContent);
              break;

            case "tool_call":
              // Show tool call in messages
              const toolCallMessage: Message = {
                type: "ai",
                content: "",
                tool_calls: [
                  {
                    name: streamEvent.data.name as string,
                    args: streamEvent.data.args as Record<string, unknown>,
                    id: streamEvent.data.id as string | undefined,
                  },
                ],
              };
              setConversation((prev) =>
                prev
                  ? {
                      ...prev,
                      messages: [...prev.messages, toolCallMessage],
                    }
                  : prev
              );
              // Reset streaming content for next response
              accumulatedContent = "";
              setStreamingContent("");
              break;

            case "tool_output":
              // Show tool output
              const toolOutputMessage: Message = {
                type: "tool",
                content: streamEvent.data.content as string,
                tool_name: streamEvent.data.tool_name as string,
                tool_call_id: streamEvent.data.tool_call_id as string | undefined,
              };
              setConversation((prev) =>
                prev
                  ? {
                      ...prev,
                      messages: [...prev.messages, toolOutputMessage],
                    }
                  : prev
              );
              break;

            case "message_end":
              // Add final AI message if we have accumulated content
              if (accumulatedContent) {
                const aiMessage: Message = {
                  type: "ai",
                  content: accumulatedContent,
                };
                setConversation((prev) =>
                  prev
                    ? {
                        ...prev,
                        messages: [...prev.messages, aiMessage],
                      }
                    : prev
                );
              }
              setStreamingContent("");
              setStreaming(false);
              ws.close();
              // Notify parent that conversation may have updated (e.g., title from first message)
              onConversationUpdate?.();
              break;

            case "error":
              onError(streamEvent.data.message as string);
              setStreaming(false);
              ws.close();
              break;
          }
        } catch {
          console.error("Failed to parse WebSocket message");
        }
      };

      ws.onerror = () => {
        onError("WebSocket connection error");
        setStreaming(false);
      };

      ws.onclose = () => {
        setStreaming(false);
        wsRef.current = null;
      };
    },
    [conversation, conversationId, onError, streaming]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingDots />
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <p className="text-red-700">Failed to load conversation</p>
      </div>
    );
  }

  // Build display messages including streaming content
  const displayMessages = [...conversation.messages];
  if (streamingContent) {
    displayMessages.push({
      type: "ai",
      content: streamingContent,
    });
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg flex flex-col h-[600px]">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">{conversation.title}</h3>
        <p className="text-xs text-gray-500">
          {conversation.agent_name} · {conversation.model}
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {displayMessages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No messages yet. Start the conversation below.
          </div>
        ) : (
          <>
            <MessageCards messages={displayMessages} />
            {streaming && !streamingContent && (
              <div className="mt-4 flex items-center gap-2 text-gray-500">
                <LoadingDots />
                <span className="text-sm">Agent is thinking...</span>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <MessageInput
        onSend={handleSendMessage}
        disabled={streaming}
        placeholder={streaming ? "Agent is responding..." : "Type a message..."}
      />
    </div>
  );
}
