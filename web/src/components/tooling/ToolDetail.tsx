import { useEffect, useState } from 'react';
import { toolingApi } from '../../api/tooling';
import type { ToolSchema } from '../../api/types';
import { InvokeForm } from './InvokeForm';
import { InvokeResult } from './InvokeResult';

interface ToolDetailProps {
  toolName: string;
}

export function ToolDetail({ toolName }: ToolDetailProps) {
  const [schema, setSchema] = useState<ToolSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [invoking, setInvoking] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    setLoading(true);
    setResult(null);
    setIsError(false);

    toolingApi
      .getToolSchema(toolName)
      .then(data => {
        setSchema(data);
      })
      .catch(err => {
        console.error('Failed to load tool schema:', err);
        setSchema(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [toolName]);

  const handleInvoke = async (args: Record<string, unknown>) => {
    setInvoking(true);
    setResult(null);
    setIsError(false);

    try {
      const response = await toolingApi.invokeTool(toolName, args);
      if (response.success) {
        setResult(JSON.stringify(response.result, null, 2));
        setIsError(false);
      } else {
        setResult(response.error || 'Unknown error');
        setIsError(true);
      }
    } catch (err) {
      setResult(err instanceof Error ? err.message : 'Unknown error');
      setIsError(true);
    } finally {
      setInvoking(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      <div>
        <h3 className="text-lg font-medium text-gray-900">{toolName}</h3>
        {schema?.description && (
          <p className="text-sm text-gray-600 mt-1">{schema.description}</p>
        )}
      </div>

      <InvokeForm schema={schema} onInvoke={handleInvoke} isLoading={invoking} />

      <InvokeResult result={result} isError={isError} />
    </div>
  );
}
