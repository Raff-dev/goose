import { ReloadIcon } from '@radix-ui/react-icons';

import type { TestSummary } from '../api/types';
import SurfaceCard from './SurfaceCard';

interface RunControlsProps {
  tests: TestSummary[];
  onlyFailures: boolean;
  onOnlyFailuresChange: (value: boolean) => void;
  onRunAll: () => void;
  isRunning: boolean;
  onReloadTests: () => void;
  isReloadingTests: boolean;
}

export function RunControls({
  tests,
  onlyFailures,
  onOnlyFailuresChange,
  onRunAll,
  isRunning,
  onReloadTests,
  isReloadingTests,
}: RunControlsProps) {
  return (
    <SurfaceCard className="bg-white p-4 mb-6">
      <div className="flex gap-4">
        <button
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={onRunAll}
          disabled={!tests.length || isRunning}
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
          {isRunning ? 'Running...' : 'Run All Tests'}
        </button>
        <button
          className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium border transition ${
            onlyFailures
              ? 'bg-blue-50 text-blue-700 border-blue-200'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
          }`}
          onClick={() => onOnlyFailuresChange(!onlyFailures)}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Show failing only
        </button>
        <button
          type="button"
          onClick={onReloadTests}
          disabled={isReloadingTests}
          className="flex items-center gap-2 px-4 py-2 rounded-md font-medium border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          <ReloadIcon className={`w-4 h-4 ${isReloadingTests ? 'animate-spin' : ''}`} />
          {isReloadingTests ? 'Reloading...' : 'Reload tests'}
        </button>
      </div>
    </SurfaceCard>
  );
}
