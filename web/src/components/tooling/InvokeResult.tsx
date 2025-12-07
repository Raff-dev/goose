interface InvokeResultProps {
  result: string | null;
  isError?: boolean;
}

export function InvokeResult({ result, isError = false }: InvokeResultProps) {
  if (!result) return null;

  const isErrorResult = isError || result.startsWith('Error:');

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Result</label>
      <pre
        className={`rounded-md p-3 text-sm font-mono overflow-x-auto whitespace-pre-wrap ${
          isErrorResult
            ? 'bg-red-50 border border-red-200 text-red-800'
            : 'bg-gray-50 border border-gray-200 text-gray-900'
        }`}
      >
        {result}
      </pre>
    </div>
  );
}
