import { createContext, useContext, useState, useCallback, useLayoutEffect, useRef, type ReactNode } from 'react';
import { useLocation } from 'react-router-dom';

interface TestingViewState {
  collapsedModules: Record<string, boolean>;
  dashboardScrollPosition: number;
  toggleModule: (moduleName: string) => void;
  setCollapsedModules: (modules: Record<string, boolean>) => void;
  setDashboardScrollPosition: (position: number) => void;
  saveScrollPosition: () => void;
}

const TestingViewStateContext = createContext<TestingViewState | null>(null);

export function TestingViewStateProvider({ children }: { children: ReactNode }) {
  const [collapsedModules, setCollapsedModules] = useState<Record<string, boolean>>({});
  const [dashboardScrollPosition, setDashboardScrollPosition] = useState<number>(0);
  const location = useLocation();
  const previousPathRef = useRef<string>(location.pathname);

  const toggleModule = useCallback((moduleName: string) => {
    setCollapsedModules(prev => ({
      ...prev,
      [moduleName]: !(prev[moduleName] ?? false),
    }));
  }, []);

  const saveScrollPosition = useCallback(() => {
    setDashboardScrollPosition(window.scrollY);
  }, []);

  // Track navigation and restore scroll position when coming back from detail to dashboard
  // useLayoutEffect runs synchronously before browser paint
  useLayoutEffect(() => {
    const currentPath = location.pathname;
    const previousPath = previousPathRef.current;

    const isDashboard = currentPath === '/testing';
    const wasDetail = previousPath.startsWith('/testing/tests/');

    // Coming back from detail to dashboard - restore scroll position
    if (wasDetail && isDashboard && dashboardScrollPosition > 0) {
      window.scrollTo(0, dashboardScrollPosition);
    }

    previousPathRef.current = currentPath;
  }, [location.pathname, dashboardScrollPosition]);

  return (
    <TestingViewStateContext.Provider
      value={{
        collapsedModules,
        dashboardScrollPosition,
        toggleModule,
        setCollapsedModules,
        setDashboardScrollPosition,
        saveScrollPosition,
      }}
    >
      {children}
    </TestingViewStateContext.Provider>
  );
}

export function useTestingViewState(): TestingViewState {
  const context = useContext(TestingViewStateContext);
  if (!context) {
    throw new Error('useTestingViewState must be used within a TestingViewStateProvider');
  }
  return context;
}
