import type { ExecutionRecordModel, TestResultModel, TestSummary } from '../api/types';
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
  const duration = result ? `${result.duration.toFixed(2)}s` : '—';

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
        <div>
          <div className="text-lg font-bold mb-4">Execution History</div>
          <div className="flex flex-col gap-4">
            {result.executions.map((execution, index) => (
              <ExecutionCard key={index} execution={execution} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface ExecutionCardProps {
  execution: ExecutionRecordModel;
}

function ExecutionCard({ execution }: ExecutionCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div>
        <div className="font-bold mb-2">Expectations</div>
        <div className="flex flex-col gap-2 mb-4">
          {(() => {
            const unmet = new Set<string>(execution.validation?.expectations_unmet ?? []);
            return execution.expectations.map((exp, i) => {
              const passed = !unmet.has(exp) && !!execution.validation;
              return (
                <div key={i} className="flex items-start gap-2">
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

          {execution.validation && (
            <div className="mt-2">
              <div className="font-bold mb-1">Validation:</div>
              <div className={`rounded-md border p-3 text-sm whitespace-pre-wrap ` +
                (execution.validation.success ? 'bg-green-50 border-green-100 text-green-800' : 'bg-red-50 border-red-100 text-red-800')
              }>
                {execution.validation.reasoning}
              </div>
            </div>
          )}
        </div>
        <div className="font-bold mb-2">Messages</div>
        <div>
          {execution.response && Array.isArray((execution.response as any).messages) ? (
            // If the response contains a `messages` array, render it as message cards
            <MessageCards messages={(execution.response as any).messages} />
          ) : (
            <CodeBlock value={execution.response ?? 'No response'} className="text-sm whitespace-pre-wrap" />
          )}
        </div>
      </div>
      {execution.error && (
        <div className="mt-4">
          <div className="font-bold text-red-500">Error:</div>
          <div className="text-red-500">{execution.error}</div>
        </div>
      )}
    </div>
  );
}
