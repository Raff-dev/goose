import { ChatBubbleIcon, GearIcon, PersonIcon, RocketIcon } from '@radix-ui/react-icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import CodeBlock from './CodeBlock';

type MessageType = 'human' | 'ai' | 'tool' | string;

interface ToolCall {
  name?: string;
  args?: any;
  id?: string;
}

interface Message {
  type: MessageType;
  content: string;
  tool_calls?: ToolCall[];
  tool_name?: string;
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

export function MessageCards({ messages }: MessageCardsProps) {
  return (
    <div className="flex flex-col gap-3">
      {messages.map((m, i) => {
        const isHuman = m.type === 'human';
        const isAI = m.type === 'ai';
        const isTool = m.type === 'tool';

        // Render all messages in card wrappers for consistent alignment.
        // Backgrounds are fully transparent per request so the visual
        // appearance stays minimal while layout remains consistent.
        const containerClass = 'rounded-lg shadow-sm border border-gray-200 p-3 bg-transparent';

        // Icon background colors (rounded colored rectangles). Use
        // darker shades for higher opacity/contrast.
        const iconBgClass = isHuman
          ? 'bg-blue-800/60'
          : isAI
          ? 'bg-violet-800/60'
          : isTool
          ? 'bg-orange-800/60'
          : 'bg-gray-600/60';

        const icon = isHuman ? (
          <PersonIcon className="w-5 h-5 text-white opacity-100" aria-hidden />
        ) : isAI ? (
          <RocketIcon className="w-5 h-5 text-white opacity-100" aria-hidden />
        ) : isTool ? (
          <GearIcon className="w-5 h-5 text-white opacity-100" aria-hidden />
        ) : (
          <ChatBubbleIcon className="w-5 h-5 text-white opacity-100" aria-hidden />
        );

        // If content parses as JSON, show it as a formatted code block.
        const parsed = tryParseJSON(m.content);
        const contentIsJSON = parsed !== null;

        return (
          <div key={i} className={containerClass}>
            <div className={`flex items-start gap-3 ${isHuman ? '' : 'py-3'}`}>
              <div className="flex-shrink-0">
                <div className={`w-10 h-10 flex items-center justify-center rounded-md ${iconBgClass}`}>
                  {icon}
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div className="flex flex-col">
                      {m.tool_calls && m.tool_calls.length > 0 && (
                        <div className="text-xs font-semibold mb-1">Tool calls</div>
                      )}
                      {m.tool_name && (
                        <>
                          <div className="text-xs font-semibold mb-1">Tool response</div>
                          <div className="text-xs">{m.tool_name}</div>
                        </>
                      )}
                    </div>
                  <div />
                </div>

                <div className="mt-2 text-base text-gray-900">
                  {contentIsJSON ? (
                    <CodeBlock value={parsed} />
                  ) : (
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      className="prose max-w-none text-gray-900 prose-p:my-2 prose-pre:bg-slate-900 prose-pre:text-white prose-base:text-base"
                      components={{
                        code({ inline, children, ...props }) {
                          if (inline) {
                            return (
                              <code className="bg-gray-100 px-1 rounded" {...props}>
                                {children}
                              </code>
                            );
                          }
                          return <CodeBlock value={String(children)} />;
                        },
                      }}
                    >
                      {m.content}
                    </ReactMarkdown>
                  )}
                </div>

                {m.tool_calls && m.tool_calls.length > 0 && (
                  <div className="mt-2">
                    <div className="flex flex-col gap-1">
                      {m.tool_calls.map((tc, idx) => (
                        <div key={idx} className="text-xs">
                          <div className="font-medium">{tc.name ?? tc.id ?? 'call'}</div>
                          {tc.args != null && (
                            <div className="mt-1">
                              <CodeBlock value={tc.args} className="mt-1" />
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default MessageCards;
