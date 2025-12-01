import { useState } from 'react';

interface GlobalErrorProps {
  error: string | null;
}

export function GlobalError({ error }: GlobalErrorProps) {
  const [isVisible, setIsVisible] = useState(true);

  if (!error || !isVisible) return null;

  return (
    <div className="bg-red-500 text-white p-4 mb-4 rounded-md border border-red-600">
      <div className="font-bold">Test Suite Error!</div>
      <div>{error}</div>
      <button
        className="mt-2 px-3 py-1 text-sm border border-white rounded hover:bg-white hover:text-red-800 transition"
        onClick={() => setIsVisible(false)}
      >
        Dismiss
      </button>
    </div>
  );
}
