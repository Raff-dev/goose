import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

interface ToolingViewState {
  listScrollPosition: number;
  detailScrollPosition: number;
  collapsedGroups: Record<string, boolean>;
  selectedTool: string | null;
  toolResult: unknown | null;
  toolIsError: boolean;
  toggleGroup: (groupName: string) => void;
  setSelectedTool: (tool: string | null) => void;
  setToolResult: (result: unknown | null, isError: boolean) => void;
  setListScrollPosition: (position: number) => void;
  setDetailScrollPosition: (position: number) => void;
}

const ToolingViewStateContext = createContext<ToolingViewState | null>(null);

export function ToolingViewStateProvider({ children }: { children: ReactNode }) {
  const [listScrollPosition, setListScrollPosition] = useState<number>(0);
  const [detailScrollPosition, setDetailScrollPosition] = useState<number>(0);
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [toolResult, setToolResultState] = useState<unknown | null>(null);
  const [toolIsError, setToolIsError] = useState<boolean>(false);

  const toggleGroup = useCallback((groupName: string) => {
    setCollapsedGroups(prev => ({
      ...prev,
      [groupName]: !(prev[groupName] ?? false),
    }));
  }, []);

  const setToolResult = useCallback((result: unknown | null, isError: boolean) => {
    setToolResultState(result);
    setToolIsError(isError);
  }, []);

  return (
    <ToolingViewStateContext.Provider
      value={{
        listScrollPosition,
        detailScrollPosition,
        collapsedGroups,
        selectedTool,
        toolResult,
        toolIsError,
        toggleGroup,
        setSelectedTool,
        setToolResult,
        setListScrollPosition,
        setDetailScrollPosition,
      }}
    >
      {children}
    </ToolingViewStateContext.Provider>
  );
}

export function useToolingViewState(): ToolingViewState {
  const context = useContext(ToolingViewStateContext);
  if (!context) {
    throw new Error('useToolingViewState must be used within a ToolingViewStateProvider');
  }
  return context;
}
