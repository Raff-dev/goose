import type { ExecutionRecordModel, TestResultModel, TestSummary } from '../api/types';

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
          <div className="text-xl font-bold">{test.name}</div>
          <div className="text-sm text-gray-500">{test.module}</div>
          <span className={`inline-block px-2 py-1 text-xs font-semibold rounded ${status === 'passed' ? 'bg-green-100 text-green-800' : status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800'}`}>
            {status === 'passed' ? 'Passed' : status === 'failed' ? 'Failed' : 'Not Run'}
          </span>
          <div>Duration: {duration}</div>
          {test.docstring && <div>{test.docstring}</div>}
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
          {execution.expectations.map((exp, i) => (
            <div key={i}>• {exp}</div>
          ))}
          {execution.validation && (
            <div>
              <div className="font-bold">Validation:</div>
              <div className={execution.validation.success ? 'text-green-500' : 'text-red-500'}>
                {execution.validation.reasoning}
              </div>
              {execution.validation.expectations_unmet.length > 0 && (
                <div>
                  <div>Unmet expectations:</div>
                  <div className="flex flex-col gap-1">
                    {execution.validation.expectations_unmet.map((unmet, i) => (
                      <div key={i} className="text-red-500">• {unmet}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
        <div className="font-bold mb-2">Messages</div>
        <pre className="text-sm whitespace-pre-wrap bg-gray-50 p-2 rounded border">
          {execution.response ? JSON.stringify(execution.response, null, 2) : 'No response'}
        </pre>
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
