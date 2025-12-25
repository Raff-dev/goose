import { useEffect, useState } from 'react';
import { toolingApi } from '../api/tooling';
import type { ToolSummary } from '../api/types';
import { ToolDetail, ToolList } from '../components/tooling';
import { useGlobalError } from '../context/GlobalErrorContext';
import { getErrorMessage } from '../utils/errors';

export function ToolingView() {
  const [tools, setTools] = useState<ToolSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [reloading, setReloading] = useState(false);
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const { setError } = useGlobalError();

  const fetchTools = async () => {
    try {
      const data = await toolingApi.listTools();
      setTools(data);
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleReload = async () => {
    setReloading(true);
    try {
      const data = await toolingApi.reloadTools();
      setTools(data);
      setError(null);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setReloading(false);
    }
  };

  useEffect(() => {
    void fetchTools();
  }, [setError]);

  if (loading) {
    return <div className="text-center py-8">Loading tools...</div>;
  }

  if (tools.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <h3 className="text-lg font-medium text-yellow-800 mb-2">No Tools Available</h3>
        <p className="text-yellow-700">
          No tools are registered. Add tools to your GooseApp configuration:
        </p>
        <pre className="mt-4 bg-yellow-100 rounded p-3 text-left text-sm overflow-x-auto">
{`from goose import GooseApp
from my_agent.tools import get_products, create_order

app = GooseApp(
    tools=[get_products, create_order],
)`}
        </pre>
        <button
          onClick={handleReload}
          disabled={reloading}
          className="mt-4 px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
        >
          {reloading ? 'Reloading...' : 'Reload Tools'}
        </button>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-8rem)]">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
        {/* Tool List */}
        <div className="lg:col-span-1 overflow-y-auto min-h-0 scrollbar-hide">
          <ToolList
            tools={tools}
            selectedTool={selectedTool}
            onSelectTool={setSelectedTool}
            onReload={handleReload}
            reloading={reloading}
          />
        </div>

        {/* Tool Details & Invoke */}
        <div className="lg:col-span-2 overflow-y-auto min-h-0 scrollbar-hide">
          {selectedTool ? (
            <ToolDetail toolName={selectedTool} />
          ) : (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center text-gray-500">
              Select a tool to view details and invoke it
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
