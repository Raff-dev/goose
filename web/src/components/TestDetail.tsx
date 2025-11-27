import type { TestResultModel, TestSummary } from '../api/types';
import CodeBlock from './CodeBlock';
import MessageCards from './MessageCards';

interface TestDetailProps {
  test: TestSummary;
  result?: TestResultModel;
  onBack: () => void;
  onRunTest: (testName: string) => void;
}

export function TestDetail({ test, result, onBack, onRunTest }: TestDetailProps) {
  const status = result ? (result.passed ? 'passed' : 'failed') : 'not-run';

  return (
    <div>
      <div className="flex gap-4 mb-4">
        <button
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          onClick={onBack}
        >
          Back to Dashboard
        </button>
        <button
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          onClick={() => onRunTest(test.qualified_name)}
        >
          Run Test
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-4">
        <div className="flex flex-col gap-2">
          <div>
            <div className="text-xl font-bold">{test.name}</div>
            <div className="text-sm text-gray-500">{test.module}</div>
            <div className="mt-2">
              {(() => {
                const statusColor =
                  status === 'passed' ? 'bg-green-50 text-green-700' :
                  status === 'failed' ? 'bg-red-50 text-red-700' :
                  'bg-gray-100 text-gray-500';
                const statusLabel =
                  status === 'passed' ? 'Passed' :
                  status === 'failed' ? 'Failed' :
                  'Not Run';
                const durationNum = result?.duration;
                return (
                  <span className={`inline-flex items-center text-xs font-semibold px-2 py-1 rounded ${statusColor}`}>
                    {statusLabel}{durationNum !== undefined && (status === 'passed' || status === 'failed') ? ` (${durationNum.toFixed(2)}s)` : ''}
                  </span>
                );
              })()}
            </div>
          </div>
          {test.docstring && <div className="italic text-sm text-gray-700">{test.docstring}</div>}
        </div>
      </div>

      {result && (
        <div className="flex flex-col gap-6">
          <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="text-lg font-bold mb-3">Test Case</div>
            {result.query && (
              <div className="mb-4">
                <div className="text-sm font-semibold text-gray-600 mb-1">Prompt</div>
                <CodeBlock value={result.query} className="text-sm" />
              </div>
            )}
            <div>
              <div className="text-sm font-semibold text-gray-600 mb-2">Expected Tool Calls</div>
              {result.expected_tool_calls.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {result.expected_tool_calls.map((tool) => (
                    <span key={tool} className="px-2 py-1 text-xs font-semibold rounded bg-gray-100 text-gray-700 border border-gray-200">
                      {tool}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500">No specific tool expectations.</div>
              )}
            </div>
          </section>

          <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="text-lg font-bold mb-3">Expectations</div>
            {result.expectations.length === 0 ? (
              <div className="text-sm text-gray-500">No expectations were recorded for this test.</div>
            ) : (
              <div className="flex flex-col gap-2">
                {(() => {
                  const unmet = new Set(result.expectations_unmet ?? []);
                  return result.expectations.map((exp, index) => {
                  const passed = !unmet.has(exp);
                  return (
                    <div key={`${exp}-${index}`} className="flex items-start gap-2">
                      <span className={passed ? 'text-green-600' : 'text-red-600'}>
                        {passed ? (
                          <svg className="w-4 h-4 mt-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                        ) : (
                          <svg className="w-4 h-4 mt-1" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                        )}
                      </span>
                      <div className={passed ? 'text-gray-900' : 'text-gray-700'}>{exp}</div>
                    </div>
                    );
                  });
                })()}
              </div>
            )}
          </section>

          <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="text-lg font-bold mb-3">Agent Response</div>
            {result.response && Array.isArray((result.response as any).messages) ? (
              <MessageCards messages={(result.response as any).messages} />
            ) : (
              <CodeBlock value={result.response ?? 'No response captured.'} className="text-sm whitespace-pre-wrap" />
            )}
          </section>

          {result.error && (
            <section className="bg-white rounded-lg shadow-sm border border-red-200 p-4">
              <div className="text-lg font-bold text-red-600 mb-2">Error</div>
              <div className="text-sm text-red-700 whitespace-pre-wrap">{result.error}</div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
