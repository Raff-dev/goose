import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

interface ChattingViewState {
  selectedConversationId: string | null;
  setSelectedConversationId: (id: string | null) => void;
}

const ChattingViewStateContext = createContext<ChattingViewState | null>(null);

export function ChattingViewStateProvider({ children }: { children: ReactNode }) {
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);

  return (
    <ChattingViewStateContext.Provider
      value={{
        selectedConversationId,
        setSelectedConversationId,
      }}
    >
      {children}
    </ChattingViewStateContext.Provider>
  );
}

export function useChattingViewState(): ChattingViewState {
  const context = useContext(ChattingViewStateContext);
  if (!context) {
    throw new Error('useChattingViewState must be used within a ChattingViewStateProvider');
  }
  return context;
}
