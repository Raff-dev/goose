
import { MouseEvent } from 'react';

import type { TestResultModel } from '../api/types';

function getActualToolCalls(result: TestResultModel | undefined): string[] {
  if (!result?.response?.messages) return [];
  const messages = result.response.messages as Array<{ tool_calls?: Array<{ name: string }> }>;
  return messages.flatMap(m => m.tool_calls?.map(tc => tc.name) ?? []);
}

function getExtraToolCalls(result: TestResultModel | undefined): string[] {
  if (!result) return [];
  const actual = new Set(getActualToolCalls(result));
  const expected = new Set(result.expected_tool_calls);
  return [...actual].filter(name => !expected.has(name));
}

interface TestCardProps {
  name: string;
  status: 'passed' | 'failed' | 'queued' | 'running' | 'not-run';
  duration?: number;
  error?: string;
  result?: TestResultModel | undefined;
  onViewDetails: () => void;
  onRunTest: () => void;
  detailsHref: string;
}

export function TestCard({ name, status, duration, error, result, onViewDetails, onRunTest, detailsHref }: TestCardProps) {
  const failureType = result?.error_type ?? null;
  const totalTokens = result?.total_tokens ?? 0;
  const extraToolCalls = getExtraToolCalls(result);
  const hasExtraToolCalls = status === 'passed' && extraToolCalls.length > 0;
  const statusColor =
    status === 'passed' ? 'bg-green-50 text-green-700' :
    status === 'failed' ? 'bg-red-50 text-red-800' :
    status === 'queued' ? 'bg-yellow-50 text-yellow-700' :
    status === 'running' ? 'bg-blue-50 text-blue-700' :
    'bg-gray-100 text-gray-500';
  const statusLabel =
    status === 'passed' ? 'Passed' :
    status === 'failed' ? 'Failed' :
    status === 'queued' ? 'Queued' :
    status === 'running' ? 'Running' :
    'Not Run';
  const badgeIcon = status === 'passed'
    ? (<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>)
    : status === 'failed'
    ? (<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>)
    : status === 'queued'
    ? (<svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" /></svg>)
    : status === 'running'
    ? (<svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" strokeOpacity="0.25" /><path d="M12 2a10 10 0 0 1 10 10" /></svg>)
    : null;
  const durationLabel = duration !== undefined && (status === 'passed' || status === 'failed')
    ? `${duration.toFixed(2)}s`
    : null;
  return (
    <div className="card flex flex-col gap-2 min-h-[170px]">
      <div className="flex items-center gap-2 mb-1 min-w-0">
        <span className={`icon-circle ${statusColor}`}>{badgeIcon}</span>
        <span className="font-semibold text-lg text-gray-900 truncate" title={name}>{name}</span>
      </div>
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-xs font-semibold px-2 py-1 rounded ${statusColor}`}>{statusLabel}{durationLabel ? ` (${durationLabel})` : ''}</span>
      </div>
      {failureType && status !== 'queued' && status !== 'running' && (
        <div className="mb-2">
          <span className={`text-xs font-semibold px-2 py-1 rounded-full bg-red-50 text-red-800 border border-red-100`}>
            {failureType === 'tool_call'
              ? 'Tool Call Mismatch'
              : failureType === 'expectation'
              ? 'Expectations Unmet'
              : failureType === 'validation'
              ? 'Validation Failure'
              : 'Unexpected Error'}
          </span>
        </div>
      )}
      {hasExtraToolCalls && (
        <div className="mb-2">
          <span
            className="text-xs font-semibold px-2 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-100"
            title={`Extra tools: ${extraToolCalls.join(', ')}`}
          >
            Extra Tool Calls
          </span>
        </div>
      )}
      {/* Error details are intentionally omitted from the card; use View Details for full context */}
      <div className="mt-auto flex justify-end gap-2">
        <button
          className={
            `flex items-center gap-1 border rounded-md px-3 py-1 text-sm font-medium transition ` +
            (status === 'running' || status === 'queued'
              ? 'border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed opacity-70'
              : 'border-gray-300 text-gray-700 hover:bg-gray-50')
          }
          onClick={onRunTest}
          disabled={status === 'running' || status === 'queued'}
          title={status === 'running' || status === 'queued' ? 'Test is running or queued' : 'Run test'}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
          Run
        </button>
        <a
          href={detailsHref}
          onClick={(event: MouseEvent<HTMLAnchorElement>) => {
            if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
              return;
            }
            event.preventDefault();
            onViewDetails();
          }}
          className="border border-gray-300 rounded-md px-4 py-1 text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
        >
          View Details
        </a>
      </div>
    </div>
  );
}
