import { ChatBubbleIcon, GearIcon, PersonIcon, RocketIcon } from '@radix-ui/react-icons';

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

function escapeHtml(unsafe: string) {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Minimal Markdown -> HTML converter for a safe subset:
 * - fenced code blocks ```code```
 * - inline code `code`
 * - bold **text**
 * - italic *text*
 * - links [text](href)
 * - unordered lists starting with `- `
 * This implementation first escapes HTML to avoid injection, then
 * applies simple regex-based transforms. It's intentionally small to
 * avoid adding a dependency.
 */
function renderMarkdownToHtml(md: string) {
  if (!md) return '';
  // Normalize line endings
  let text = String(md).replace(/\r\n?/g, '\n');

  // Escape HTML first
  text = escapeHtml(text);

  // Fenced code blocks ```\n...\n```
  text = text.replace(/```([\s\S]*?)```/g, (_m, code) => {
    return `<pre class="bg-gray-900 text-white p-2 rounded"><code>${escapeHtml(code)}</code></pre>`;
  });

  // Unordered lists: convert lines starting with - to <ul>
  const lines = text.split('\n');
  let inList = false;
  const outLines: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (/^-\s+/.test(trimmed)) {
      if (!inList) {
        inList = true;
        outLines.push('<ul class="list-disc pl-5">');
      }
      const item = trimmed.replace(/^-\s+/, '');
      outLines.push(`<li>${item}</li>`);
    } else {
      if (inList) {
        inList = false;
        outLines.push('</ul>');
      }
      outLines.push(line);
    }
  }
  if (inList) outLines.push('</ul>');
  text = outLines.join('\n');

  // Inline code
  text = text.replace(/`([^`]+)`/g, (_m, code) => `<code class="bg-gray-100 px-1 rounded">${escapeHtml(code)}</code>`);

  // Bold **text**
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Italic *text* (avoid replacing inside strong)
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Links [text](url)
  text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_m, label, href) => `<a class="underline text-blue-600" href="${href}">${label}</a>`);

  // Convert remaining line breaks to <br /> for simple paragraphs
  text = text.replace(/\n/g, '<br/>');

  return text;
}

export function MessageCards({ messages }: MessageCardsProps) {
  return (
    <div className="flex flex-col gap-3">
      {messages.map((m, i) => {
        const isHuman = m.type === 'human';
        const isAI = m.type === 'ai';
        const isTool = m.type === 'tool';

        // Separate background color from label text color so the
        // message body keeps the default text color.
        const bgBgClass = isHuman
          ? 'bg-blue-50'
          : isAI
          ? 'bg-violet-50'
          : isTool
          ? 'bg-orange-50'
          : 'bg-gray-50';

        const labelColorClass = isHuman
          ? 'text-blue-800'
          : isAI
          ? 'text-violet-800'
          : isTool
          ? 'text-orange-800'
          : 'text-gray-800';

        // Use Radix icons for consistent monochrome icons. Keep icons
        // neutral (gray) and slightly opaque so they don't dominate.
        const icon = isHuman ? (
          <PersonIcon className="w-6 h-6 text-gray-600 opacity-80" aria-hidden />
        ) : isAI ? (
          <RocketIcon className="w-6 h-6 text-gray-600 opacity-80" aria-hidden />
        ) : isTool ? (
          <GearIcon className="w-6 h-6 text-gray-600 opacity-80" aria-hidden />
        ) : (
          <ChatBubbleIcon className="w-6 h-6 text-gray-600 opacity-80" aria-hidden />
        );

        // If content parses as JSON, show it as a formatted code block.
        const parsed = tryParseJSON(m.content);
        const contentIsJSON = parsed !== null;

        return (
          <div key={i} className={`rounded-lg shadow-sm border border-gray-200 p-3 ${bgBgClass} bg-opacity-90`}>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 text-2xl">{icon}</div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <div className={`font-semibold capitalize ${labelColorClass}`}>{m.type}</div>
                  {m.tool_name && <div className="text-xs opacity-80">{m.tool_name}</div>}
                </div>

                <div className="mt-2 text-sm text-gray-900">
                  {contentIsJSON ? (
                    <pre className="bg-black bg-opacity-80 text-white text-xs p-2 rounded overflow-auto">{prettyJSON(parsed)}</pre>
                  ) : (
                    <div className="prose max-w-none text-gray-900" dangerouslySetInnerHTML={{ __html: renderMarkdownToHtml(m.content) }} />
                  )}
                </div>

                {m.tool_calls && m.tool_calls.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs font-semibold mb-1">Tool calls</div>
                    <div className="flex flex-col gap-1">
                      {m.tool_calls.map((tc, idx) => (
                        <div key={idx} className="text-xs">
                          <div className="font-medium">{tc.name ?? tc.id ?? 'call'}</div>
                          {tc.args != null && (
                            <pre className="bg-gray-900 text-white text-xs p-2 rounded mt-1 overflow-auto">{prettyJSON(tc.args)}</pre>
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
