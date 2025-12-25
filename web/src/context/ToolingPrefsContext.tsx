import { createContext, useContext, useState, type ReactNode } from 'react';

interface ToolingPrefs {
  renderMarkdown: boolean;
  useRawJson: boolean;
  setRenderMarkdown: (value: boolean) => void;
  setUseRawJson: (value: boolean) => void;
}

const ToolingPrefsContext = createContext<ToolingPrefs | null>(null);

export function ToolingPrefsProvider({ children }: { children: ReactNode }) {
  const [renderMarkdown, setRenderMarkdown] = useState(true);
  const [useRawJson, setUseRawJson] = useState(false);

  return (
    <ToolingPrefsContext.Provider
      value={{ renderMarkdown, useRawJson, setRenderMarkdown, setUseRawJson }}
    >
      {children}
    </ToolingPrefsContext.Provider>
  );
}

export function useToolingPrefs(): ToolingPrefs {
  const context = useContext(ToolingPrefsContext);
  if (!context) {
    throw new Error('useToolingPrefs must be used within a ToolingPrefsProvider');
  }
  return context;
}
