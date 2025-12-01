import { useEffect, useMemo, useState } from 'react';
import type { TestResultModel } from './api/types';
import { GlobalError } from './components/GlobalError';
import { RunControls } from './components/RunControls';
import { Summary } from './components/Summary';
import { TestDetail } from './components/TestDetail';
import { TestGrid } from './components/TestGrid';
import { useCreateRun, useRun, useRuns, useTests } from './hooks';

function App() {
  const {
    data: tests = [],
    isLoading: testsLoading,
    isFetching: testsFetching,
    refetch: refetchTests,
  } = useTests();
  const { data: runs = [], isLoading: runsLoading } = useRuns();
  const createRunMutation = useCreateRun();

  const [view, setView] = useState<'dashboard' | 'detail'>('dashboard');
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [onlyFailures, setOnlyFailures] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const { data: currentJob } = useRun(currentJobId || '', !!currentJobId);

  // Aggregate latest results for each test from all runs
  const resultsMap = useMemo(() => {
    const map = new Map<string, TestResultModel>();
    // Sort runs by created_at desc
    const sortedRuns = [...runs].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    for (const run of sortedRuns) {
      for (const result of run.results) {
        if (!map.has(result.qualified_name)) {
          map.set(result.qualified_name, result);
        }
      }
    }
    return map;
  }, [runs]);

  // Compute status for each test
  const statusMap = useMemo(() => {
    const map = new Map<string, string>();

    // Get all test names that have been run recently
    const allTestNames = new Set<string>();
    for (const run of runs) {
      for (const testName of run.tests) {
        allTestNames.add(testName);
      }
    }

    // First, set status based on per-test statuses from jobs (most recent first)
    for (const run of runs) {
      if (run.test_statuses) {
        for (const [testName, status] of Object.entries(run.test_statuses)) {
          if (!map.has(testName)) {
            map.set(testName, status);
          }
        }
      }
    }

    // Then, for tests without status, set from results
    for (const [name, result] of resultsMap) {
      if (!map.has(name)) {
        map.set(name, result.passed ? 'passed' : 'failed');
      }
    }

    // Any test that hasn't been touched should be 'not-run'
    for (const testName of allTestNames) {
      if (!map.has(testName)) {
        map.set(testName, 'not-run');
      }
    }

    return map;
  }, [runs, resultsMap]);

  useEffect(() => {
    if (currentJob && (currentJob.status === 'succeeded' || currentJob.status === 'failed')) {
      setCurrentJobId(null);
    }
  }, [currentJob]);

  const handleViewDetails = (testName: string) => {
    // push a navigable URL so browser back/forward works
    try {
      const url = `/tests/${encodeURIComponent(testName)}`;
      window.history.pushState({}, '', url);
    } catch (e) {
      // ignore
    }
    setSelectedTest(testName);
    setView('detail');
  };

  const handleBack = () => {
    // Try to go back in history first so browser back behaves naturally.
    if (window.history.length > 1) {
      window.history.back();
      // also optimistically update UI
      setView('dashboard');
      setSelectedTest(null);
      return;
    }
    setView('dashboard');
    setSelectedTest(null);
  };

  // Sync app state with URL on mount and when user navigates with back/forward
  useEffect(() => {
    const syncFromLocation = () => {
      const path = window.location.pathname || '/';
      const match = path.match(/^\/tests\/(.+)$/);
      if (match) {
        const testName = decodeURIComponent(match[1]);
        setSelectedTest(testName);
        setView('detail');
      } else {
        setSelectedTest(null);
        setView('dashboard');
      }
    };

    // initial sync
    syncFromLocation();

    const onPop = () => syncFromLocation();
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const handleRunTest = async (testName: string) => {
    await createRunMutation.mutateAsync({ tests: [testName] });
  };

  const handleReloadTests = () => {
    void refetchTests();
  };

  if (testsLoading || runsLoading) {
    return <div>Loading...</div>;
  }

  const selectedTestData = tests.find(t => t.qualified_name === selectedTest);
  const selectedResult = selectedTest ? resultsMap.get(selectedTest) : undefined;
  const latestRun = runs[0];

  const isRunning = runs.some(job => job.status === 'running' || job.status === 'queued');

  const handleRunAll = async () => {
    await createRunMutation.mutateAsync(undefined);
  };

  return (
    <div className="max-w-7xl mx-auto py-8">
      <GlobalError error={latestRun?.error || null} />
      {view === 'dashboard' ? (
        <>
          <Summary tests={tests} resultsMap={resultsMap} />
          <RunControls
            tests={tests}
            onlyFailures={onlyFailures}
            onOnlyFailuresChange={setOnlyFailures}
            onRunAll={handleRunAll}
            isRunning={isRunning}
            onReloadTests={handleReloadTests}
            isReloadingTests={testsFetching}
          />
          <TestGrid
            tests={tests}
            resultsMap={resultsMap}
            statusMap={statusMap}
            onlyFailures={onlyFailures}
            onViewDetails={handleViewDetails}
            onRunTest={handleRunTest}
          />
        </>
      ) : selectedTestData ? (
        <TestDetail
          test={selectedTestData}
          result={selectedResult}
          onBack={handleBack}
          onRunTest={handleRunTest}
        />
      ) : null}
    </div>
  );
}

export default App;
