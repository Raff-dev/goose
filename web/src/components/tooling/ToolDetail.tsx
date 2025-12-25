import { useEffect, useState } from 'react';
import { toolingApi } from '../../api/tooling';
import type { ToolSchema } from '../../api/types';
import { useGlobalError } from '../../context/GlobalErrorContext';
import { useToolingPrefs } from '../../context/ToolingPrefsContext';
import { getErrorMessage } from '../../utils/errors';
import { InvokeForm } from './InvokeForm';
import { InvokeResult } from './InvokeResult';

interface ToolDetailProps {
  toolName: string;
}

export function ToolDetail({ toolName }: ToolDetailProps) {
  const [schema, setSchema] = useState<ToolSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [invoking, setInvoking] = useState(false);
  const [result, setResult] = useState<unknown | null>(null);
  const [isError, setIsError] = useState(false);
  const { renderMarkdown, useRawJson, setRenderMarkdown, setUseRawJson } = useToolingPrefs();
  const { setError: setGlobalError } = useGlobalError();

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
        setGlobalError(getErrorMessage(err));
      })
      .finally(() => {
        setLoading(false);
      });
  }, [toolName, setGlobalError]);

  const handleInvoke = async (args: Record<string, unknown>) => {
    setInvoking(true);
    setResult(null);
    setIsError(false);

    try {
      const response = await toolingApi.invokeTool(toolName, args);
      if (response.success) {
        setResult(response.result ?? null);
        setIsError(false);
      } else {
        setResult(response.error || 'Unknown error');
        setIsError(true);
      }
    } catch (err) {
      // For HTTP/network errors, show in global error
      console.error('Tool invoke error:', err);
      const errorMessage = getErrorMessage(err) || 'Unknown error';
      console.log('Extracted error message:', errorMessage);
      setGlobalError(errorMessage);
      setResult(errorMessage);
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
        <div className="flex items-start justify-between gap-4 mt-1">
          {schema?.description && (
            <p className="text-sm text-gray-600 flex-1">{schema.description}</p>
          )}
          <div className="flex flex-col items-end gap-2 flex-shrink-0">
            <Toggle
              label="Markdown"
              checked={renderMarkdown}
              onChange={setRenderMarkdown}
            />
            <Toggle
              label="Raw JSON"
              checked={useRawJson}
              onChange={setUseRawJson}
            />
          </div>
        </div>
      </div>

      <InvokeForm
        schema={schema}
        onInvoke={handleInvoke}
        isLoading={invoking}
        useRawJson={useRawJson}
      />

      <InvokeResult
        result={result}
        isError={isError}
        renderMarkdown={renderMarkdown}
      />
    </div>
  );
}

interface ToggleProps {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}

function Toggle({ label, checked, onChange }: ToggleProps) {
  return (
    <label className="inline-flex items-center gap-2 cursor-pointer select-none">
      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        onChange={e => onChange(e.target.checked)}
      />
      <span
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-blue-600' : 'bg-slate-200'
        }`}
        aria-hidden="true"
      >
        <span
          className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0.5'
          }`}
        />
      </span>
      <span className="text-sm text-gray-500">{label}</span>
    </label>
  );
}
