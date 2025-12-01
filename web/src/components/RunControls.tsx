import { ReloadIcon } from '@radix-ui/react-icons';
import { useEffect, useState } from 'react';

import type { TestSummary } from '../api/types';
import LoadingDots from './LoadingDots';
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
  const runDisabled = !tests.length || isRunning;
  const exitDelayMs = 600;
  const [isReloadIconSpinning, setIsReloadIconSpinning] = useState(false);

  const handleReloadClick = () => {
    setIsReloadIconSpinning(true);
    onReloadTests();
  };

  useEffect(() => {
    if (isReloadingTests) {
      setIsReloadIconSpinning(true);
      return;
    }

    if (!isReloadingTests && isReloadIconSpinning) {
      const timeoutId = window.setTimeout(() => setIsReloadIconSpinning(false), exitDelayMs);
      return () => window.clearTimeout(timeoutId);
    }
    return undefined;
  }, [isReloadingTests, isReloadIconSpinning]);

  return (
    <SurfaceCard className="bg-white p-4 mb-6">
      <div className="flex gap-4">
        <button
          className={`inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold text-white shadow-lg transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 ${runDisabled ? 'cursor-not-allowed bg-gradient-to-r from-slate-400 to-slate-500 opacity-70' : 'bg-blue-500 hover:bg-blue-600 hover:shadow-xl'}`}
          onClick={onRunAll}
          disabled={runDisabled}
        >
          {isRunning ? (
            <LoadingDots />
          ) : null}
          {isRunning ? 'Running' : 'Run All Tests'}
        </button>
        <button
          className={`inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold border transition ${
            onlyFailures
              ? 'bg-blue-50 text-blue-700 border-blue-200 shadow'
              : 'bg-white text-slate-700 border-slate-300 hover:bg-gray-50 shadow'
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
          onClick={handleReloadClick}
          disabled={isReloadingTests}
          className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-5 py-2 text-sm font-semibold text-slate-700 shadow transition hover:bg-gray-50 disabled:opacity-50"
        >
          <span className={`inline-flex items-center justify-center ${isReloadIconSpinning ? 'animate-reload-spin' : ''}`}>
            <ReloadIcon className="w-4 h-4" />
          </span>
          {isReloadingTests ? 'Reloading...' : 'Reload tests'}
        </button>
      </div>
    </SurfaceCard>
  );
}
