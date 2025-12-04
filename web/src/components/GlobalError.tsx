import { useEffect, useRef, useState } from 'react';

import SurfaceCard from './SurfaceCard';

interface GlobalErrorProps {
  error: string | null;
  errorKey?: number;
}

export function GlobalError({ error, errorKey }: GlobalErrorProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(true);
  const [isAnimating, setIsAnimating] = useState(false);
  const prevErrorRef = useRef<string | null>(null);

  // Animate in when error appears or changes
  useEffect(() => {
    if (error && (error !== prevErrorRef.current || !isVisible)) {
      prevErrorRef.current = error;
      setShowDetails(true);
      setIsAnimating(true);
      // Trigger animation after a frame to ensure initial state is rendered
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setIsVisible(true);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        });
      });
    }
  }, [error, errorKey]);

  const handleDismiss = () => {
    setIsVisible(false);
    // Wait for animation to complete before hiding
    setTimeout(() => {
      setIsAnimating(false);
    }, 300);
  };

  if (!error || (!isVisible && !isAnimating)) return null;

  return (
    <div
      className={`transform transition-all duration-300 ease-out mb-6 ${
        isVisible
          ? 'translate-y-0 opacity-100'
          : '-translate-y-4 opacity-0'
      }`}
    >
      <SurfaceCard as="section" className="bg-white p-0 rounded-r-xl rounded-l-none">
        <div className="border border-red-100 rounded-r-xl rounded-l-none">
          <div className="flex flex-col gap-4 border-l-4 border-red-500 p-6">
            <div className="flex flex-wrap items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-700" aria-hidden="true">
                <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a1 1 0 00.86 1.5h18.64a1 1 0 00.86-1.5L13.71 3.86a1 1 0 00-1.72 0z" />
                </svg>
              </div>
              <div className="min-w-[200px] flex-1">
                <p className="text-lg font-semibold text-red-800">Test Suite Error</p>
                <p className="mt-1 text-sm text-slate-600">
                  Failed to load tests. Check the stack trace below for details.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowDetails(prev => !prev)}
                  className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-slate-900"
                  aria-expanded={showDetails}
                >
                  <svg
                    className={`h-4 w-4 transition-transform ${showDetails ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                  {showDetails ? 'Hide' : 'Show'} Details
                </button>
                <button
                  type="button"
                  onClick={handleDismiss}
                  className="inline-flex items-center gap-1 text-sm font-semibold text-slate-500 hover:text-slate-700"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Dismiss
                </button>
              </div>
            </div>
            <div
              className={`transition-all duration-300 ease-out overflow-hidden ${
                showDetails ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
              }`}
            >
              <pre className="whitespace-pre-wrap text-sm font-mono bg-slate-50 p-4 rounded-lg overflow-x-auto max-h-96 overflow-y-auto text-slate-800 border border-slate-200">
                {error}
              </pre>
            </div>
          </div>
        </div>
      </SurfaceCard>
    </div>
  );
}
