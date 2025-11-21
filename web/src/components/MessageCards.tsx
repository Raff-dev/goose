import { ChatBubbleIcon, GearIcon, PersonIcon, RocketIcon } from '@radix-ui/react-icons';
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

  // Preserve fenced code blocks by replacing them with placeholders
  // so later transforms (like replacing newlines) don't break their
  // internal formatting.
  const codeBlocks: string[] = [];
  text = text.replace(/```([\s\S]*?)```/g, (_m, code) => {
    const pre = `<pre class="bg-gray-900 text-white p-2 rounded"><code>${escapeHtml(code)}</code></pre>`;
    const idx = codeBlocks.length;
    codeBlocks.push(pre);
    return `@@CODE_BLOCK_${idx}@@`;
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

  // Paragraphize: split on two or more newlines into paragraphs. Single
  // newlines inside a paragraph become spaces (prevents excessive <br/>).
  const parts = text.split(/\n{2,}/g).map(p => p.trim()).filter(Boolean);
  text = parts.map(p => {
    // If the part is exactly a preserved code block placeholder, restore it
    const codeMatch = p.match(/^@@CODE_BLOCK_(\d+)@@$/);
    if (codeMatch) {
      return codeBlocks[Number(codeMatch[1])] || '';
    }
    // Otherwise collapse single newlines into spaces and wrap in <p>
    const inner = p.replace(/\n/g, ' ');
    return `<p>${inner}</p>`;
  }).join('\n');

  return text;
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

                        <div className="mt-2 text-sm text-gray-900">

                          {contentIsJSON ? (
                            <CodeBlock value={parsed} />
                          ) : (
                            <div className="prose max-w-none text-gray-900" dangerouslySetInnerHTML={{ __html: renderMarkdownToHtml(m.content) }} />
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
                              <CodeBlock value={tc.args} className="text-xs mt-1" />
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
