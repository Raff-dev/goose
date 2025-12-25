import type { DetailedHTMLProps, HTMLAttributes, ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import CodeBlock from '../CodeBlock';

interface InvokeResultProps {
  result: unknown | null;
  isError?: boolean;
  renderMarkdown: boolean;
}

export function InvokeResult({ result, isError = false, renderMarkdown }: InvokeResultProps) {
  if (result === null || result === undefined) {
    return null;
  }

  const resultText = typeof result === 'string' ? result : null;
  const isErrorResult = isError || (resultText !== null && resultText.startsWith('Error:'));

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Result</label>

      {isErrorResult ? (
        <pre className="rounded-md p-3 text-sm font-mono overflow-x-auto whitespace-pre-wrap bg-red-50 border border-red-200 text-red-800">
          {resultText ?? String(result)}
        </pre>
      ) : resultText !== null ? (
        renderMarkdown ? (
          <div className="rounded-md p-3 bg-gray-50 border border-gray-200">
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
              {resultText}
            </ReactMarkdown>
          </div>
        ) : (
          <pre className="rounded-md p-3 text-sm font-mono overflow-x-auto whitespace-pre-wrap bg-gray-50 border border-gray-200 text-gray-900">
            {resultText}
          </pre>
        )
      ) : (
        <CodeBlock value={result} className="border border-gray-200" />
      )}
    </div>
  );
}
