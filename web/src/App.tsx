import { useState } from 'react';
import { TestingView } from './views/TestingView';
import { ToolingView } from './views/ToolingView';

type Tab = 'testing' | 'tooling';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('testing');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Tab Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('testing')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'testing'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Testing
            </button>
            <button
              onClick={() => setActiveTab('tooling')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'tooling'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Tooling
            </button>
          </div>
        </div>
      </nav>

      {/* Tab Content */}
      <main className="max-w-7xl mx-auto py-8 px-4">
        {activeTab === 'testing' ? <TestingView /> : <ToolingView />}
      </main>
    </div>
  );
}

export default App;
