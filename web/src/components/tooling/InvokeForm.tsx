import { useEffect, useState } from 'react';
import type { ToolParameter, ToolSchema } from '../../api/types';

interface InvokeFormProps {
  schema: ToolSchema | null;
  onInvoke: (args: Record<string, unknown>) => void;
  isLoading: boolean;
}

export function InvokeForm({ schema, onInvoke, isLoading }: InvokeFormProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [useRawJson, setUseRawJson] = useState(false);
  const [rawJson, setRawJson] = useState('{}');

  // Reset values when schema changes
  useEffect(() => {
    if (schema) {
      const initial: Record<string, string> = {};
      for (const param of schema.parameters) {
        if (param.default !== undefined && param.default !== null) {
          initial[param.name] = JSON.stringify(param.default);
        } else {
          initial[param.name] = '';
        }
      }
      setValues(initial);
      setRawJson('{}');
    }
  }, [schema]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (useRawJson) {
      try {
        const parsed = JSON.parse(rawJson);
        onInvoke(parsed);
      } catch {
        alert('Invalid JSON');
      }
      return;
    }

    // Parse values based on parameter types
    const args: Record<string, unknown> = {};
    if (schema) {
      for (const param of schema.parameters) {
        const value = values[param.name];
        if (value === '' && !param.required) {
          continue;
        }
        args[param.name] = parseValue(value, param.type);
      }
    }
    onInvoke(args);
  };

  const parseValue = (value: string, type: string): unknown => {
    if (value === '') {
      return undefined;
    }
    const lowerType = type.toLowerCase();
    if (lowerType === 'integer' || lowerType === 'int') {
      return parseInt(value, 10);
    }
    if (lowerType === 'number' || lowerType === 'float') {
      return parseFloat(value);
    }
    if (lowerType === 'boolean' || lowerType === 'bool') {
      return value.toLowerCase() === 'true';
    }
    if (lowerType.startsWith('array') || lowerType.startsWith('list') || lowerType.startsWith('object') || lowerType.startsWith('dict')) {
      try {
        return JSON.parse(value);
      } catch {
        return value;
      }
    }
    return value;
  };

  if (!schema) {
    return (
      <div className="text-gray-500 text-sm">
        Loading tool schema...
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-gray-700">Parameters</h4>
        <label className="flex items-center text-sm text-gray-500">
          <input
            type="checkbox"
            checked={useRawJson}
            onChange={e => setUseRawJson(e.target.checked)}
            className="mr-2 rounded border-gray-300"
          />
          Raw JSON
        </label>
      </div>

      {useRawJson ? (
        <textarea
          value={rawJson}
          onChange={e => setRawJson(e.target.value)}
          className="w-full h-32 font-mono text-sm border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder='{"key": "value"}'
        />
      ) : schema.parameters.length === 0 ? (
        <p className="text-sm text-gray-500 italic">This tool takes no parameters.</p>
      ) : (
        <div className="space-y-3">
          {schema.parameters.map(param => (
            <ParameterInput
              key={param.name}
              param={param}
              value={values[param.name] || ''}
              onChange={v => setValues(prev => ({ ...prev, [param.name]: v }))}
            />
          ))}
        </div>
      )}

      <button
        type="submit"
        disabled={isLoading}
        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Invoking...' : 'Invoke Tool'}
      </button>
    </form>
  );
}

interface ParameterInputProps {
  param: ToolParameter;
  value: string;
  onChange: (value: string) => void;
}

function ParameterInput({ param, value, onChange }: ParameterInputProps) {
  const lowerType = param.type.toLowerCase();
  const isBool = lowerType === 'boolean' || lowerType === 'bool';
  const isNumber = lowerType === 'integer' || lowerType === 'int' || lowerType === 'number' || lowerType === 'float';
  const isComplex = lowerType.startsWith('array') || lowerType.startsWith('list') || lowerType.startsWith('object') || lowerType.startsWith('dict');

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {param.name}
        {param.required && <span className="text-red-500 ml-1">*</span>}
        <span className="text-gray-400 font-normal ml-2">({param.type})</span>
      </label>
      {param.description && (
        <p className="text-xs text-gray-500 mb-1">{param.description}</p>
      )}
      {isBool ? (
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">-- Select --</option>
          <option value="true">true</option>
          <option value="false">false</option>
        </select>
      ) : isComplex ? (
        <textarea
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={`e.g., ${lowerType.includes('array') || lowerType.includes('list') ? '["item1", "item2"]' : '{"key": "value"}'}`}
          className="w-full h-20 font-mono text-sm border border-gray-300 rounded-md p-2 focus:ring-blue-500 focus:border-blue-500"
        />
      ) : (
        <input
          type={isNumber ? 'number' : 'text'}
          value={value}
          onChange={e => onChange(e.target.value)}
          required={param.required}
          className="w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-blue-500 focus:border-blue-500"
          placeholder={param.default !== undefined && param.default !== null ? `Default: ${param.default}` : undefined}
        />
      )}
    </div>
  );
}
