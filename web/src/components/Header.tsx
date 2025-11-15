
export function Header() {
  return (
    <header className="w-full flex items-center justify-between px-8 py-4 bg-white shadow-sm border-b border-gray-200">
      <div className="flex items-center gap-3">
        <span className="icon-circle bg-blue-600 text-white">
          {/* Flask SVG icon */}
          <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
            <path d="M7 3h10M12 3v7.5M8.5 10.5h7M5 21h14a2 2 0 0 0 1.7-3.1l-5.7-8.5V3m-4 0v6.9l-5.7 8.5A2 2 0 0 0 5 21Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </span>
        <span className="font-semibold text-lg tracking-tight text-gray-900">Goose Test Dashboard</span>
      </div>
      <nav>
        <span className="text-sm text-gray-500 font-medium">Dashboard</span>
      </nav>
    </header>
  );
}
