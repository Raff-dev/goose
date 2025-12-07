import { createContext, useCallback, useContext, useState, type ReactNode } from 'react';

interface GlobalErrorContextType {
  error: string | null;
  errorKey: number;
  setError: (error: string | null) => void;
  clearError: () => void;
}

const GlobalErrorContext = createContext<GlobalErrorContextType | null>(null);

export function GlobalErrorProvider({ children }: { children: ReactNode }) {
  const [error, setErrorState] = useState<string | null>(null);
  const [errorKey, setErrorKey] = useState(0);

  const setError = useCallback((newError: string | null) => {
    setErrorState(newError);
    if (newError) {
      setErrorKey(k => k + 1);
    }
  }, []);

  const clearError = useCallback(() => {
    setErrorState(null);
  }, []);

  return (
    <GlobalErrorContext.Provider value={{ error, errorKey, setError, clearError }}>
      {children}
    </GlobalErrorContext.Provider>
  );
}

export function useGlobalError(): GlobalErrorContextType {
  const context = useContext(GlobalErrorContext);
  if (!context) {
    throw new Error('useGlobalError must be used within a GlobalErrorProvider');
  }
  return context;
}
