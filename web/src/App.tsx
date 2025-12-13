import { BrowserRouter, NavLink, Navigate, Route, Routes } from 'react-router-dom';
import { GlobalError } from './components/GlobalError';
import { GlobalErrorProvider, useGlobalError } from './context/GlobalErrorContext';
import { ChattingView } from './views/ChattingView';
import { TestingView } from './views/TestingView';
import { ToolingView } from './views/ToolingView';

function AppContent() {
  const { error, errorKey } = useGlobalError();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
      isActive
        ? 'border-blue-500 text-blue-600'
        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
    }`;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Tab Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex space-x-8">
            <NavLink to="/testing" className={linkClass}>
              Testing
            </NavLink>
            <NavLink to="/tooling" className={linkClass}>
              Tooling
            </NavLink>
            <NavLink to="/chat" className={linkClass}>
              Chat
            </NavLink>
          </div>
        </div>
      </nav>

      {/* Tab Content */}
      <main className="max-w-7xl mx-auto py-6 px-4">
        <GlobalError error={error} errorKey={errorKey} />
        <Routes>
          <Route path="/testing/*" element={<TestingView />} />
          <Route path="/tooling" element={<ToolingView />} />
          <Route path="/chat" element={<ChattingView />} />
          <Route path="*" element={<Navigate to="/testing" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <GlobalErrorProvider>
        <AppContent />
      </GlobalErrorProvider>
    </BrowserRouter>
  );
}

export default App;
