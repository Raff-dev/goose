import { ChatBubbleIcon, GearIcon, PersonIcon, RocketIcon } from '@radix-ui/react-icons';
import type { DetailedHTMLProps, HTMLAttributes, ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import CodeBlock from './CodeBlock';

type MessageType = 'human' | 'ai' | 'tool' | string;

interface TokenUsage {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

interface ToolCall {
  name: string;
  args: any;
  id?: string;
}

interface Message {
  type: MessageType;
  content: string;
  tool_calls?: ToolCall[];
  tool_name?: string;
  timestamp?: string | number | Date;
  token_usage?: TokenUsage | null;
}

interface MessageCardsProps {
  messages: Message[];
}

function tryParseJSON(text: string) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function prettyJSON(obj: any) {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
}

function formatTimestamp(value?: string | number | Date) {
  if (value === undefined || value === null) {
    return null;
  }
  const candidate = value instanceof Date ? value : new Date(value);
  if (candidate instanceof Date && !Number.isNaN(candidate.getTime())) {
    return candidate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  if (typeof value === 'string' && value.trim().length > 0) {
    return value;
  }
  return null;
}

export function MessageCards({ messages }: MessageCardsProps) {
  if (!messages || messages.length === 0) {
    return <p className="text-sm text-slate-500">No agent conversation captured for this run.</p>;
  }

  return (
    <div className="relative">
      <div className="flex flex-col gap-6">
        {messages.map((m, i) => {
          const isHuman = m.type === 'human';
          const isAI = m.type === 'ai';
          const isTool = m.type === 'tool';
          const isError = m.type === 'error';
          const bubbleTint = isHuman
            ? 'bg-blue-50 border border-blue-100'
            : isAI
            ? 'bg-white border border-slate-200'
            : isTool
            ? 'bg-emerald-50 border border-emerald-100'
            : isError
            ? 'bg-red-50 border border-red-100'
            : 'bg-white border border-slate-200';
          const avatarClass = 'bg-blue-500/85';
          const roleLabel = isHuman ? 'User Prompt' : isAI ? 'Agent Reply' : isTool ? 'Tool Output' : isError ? 'Error' : 'Message';
          const icon = isHuman ? (
            <PersonIcon className="w-5 h-5 text-white" aria-hidden />
          ) : isAI ? (
            <RocketIcon className="w-5 h-5 text-white" aria-hidden />
          ) : isTool ? (
            <GearIcon className="w-5 h-5 text-white" aria-hidden />
          ) : (
            <ChatBubbleIcon className="w-5 h-5 text-white" aria-hidden />
          );
          const parsed = tryParseJSON(m.content);
          const contentIsJSON = parsed !== null;
          const timestampLabel = formatTimestamp(m.timestamp);
          const hoverLabel = timestampLabel ?? `Message ${i + 1}`;
          const tokenCount = m.token_usage?.total_tokens;

          return (
            <div key={`${m.type}-${i}`} className="relative pl-8 group">
              <div className={`absolute left-0 top-2 flex h-10 w-10 items-center justify-center rounded-full text-white shadow-lg ${avatarClass}`} aria-hidden="true">
                {icon}
              </div>
              <div
                className={`rounded-2xl p-5 shadow-sm transition-colors ${bubbleTint}`}
                title={hoverLabel}
              >
                <div className="flex items-start justify-between">
                  <div className="text-sm font-semibold text-slate-700">{roleLabel}</div>
                  <div className="flex items-center gap-2">
                    {tokenCount !== undefined && tokenCount > 0 && (
                      <span className="text-xs text-slate-400 font-medium">
                        {tokenCount.toLocaleString()} tokens
                      </span>
                    )}
                    <span className="text-xs text-slate-500 opacity-0 transition-opacity duration-150 ease-in-out group-hover:opacity-100">
                      {hoverLabel}
                    </span>
                  </div>
                </div>
                <div className="mt-2 text-base text-slate-900">
                  {contentIsJSON ? (
                    <CodeBlock value={prettyJSON(parsed)} />
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      className="prose max-w-none text-slate-900 prose-p:my-2 prose-pre:bg-slate-900 prose-pre:text-white prose-base:text-base"
                      components={{
                        code({ inline, children, ...props }: { inline?: boolean; children?: ReactNode } & DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement>) {
                          if (inline) {
                            return (
                              <code className="bg-slate-100 px-1 rounded" {...props}>
                                {children}
                              </code>
                            );
                          }
                          return <CodeBlock value={String(children)} />;
                        },
                        table({ children, ...props }) {
                          return (
                            <div className="overflow-x-auto">
                              <table className="border-collapse border border-slate-300 [&_th]:border [&_th]:border-slate-300 [&_th]:px-3 [&_th]:py-2 [&_td]:border [&_td]:border-slate-300 [&_td]:px-3 [&_td]:py-2" {...props}>{children}</table>
                            </div>
                          );
                        },
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  )}
                </div>

                {m.tool_calls && m.tool_calls.length > 0 && (
                  <div className="mt-3 space-y-2">
                    {m.tool_calls.map((tc, idx) => (
                      <div key={idx} className="text-xs">
                        <div className="font-semibold text-slate-700">{tc.name ?? tc.id ?? 'Tool call'}</div>
                        {tc.args != null && (
                          <div className="mt-1">
                            <CodeBlock value={tc.args} className="mt-1" />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default MessageCards;
