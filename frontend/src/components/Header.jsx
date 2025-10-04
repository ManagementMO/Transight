export default function Header() {
  return (
    <header className="relative bg-gradient-to-b from-gray-50 via-white to-gray-50 border-b border-gray-200 px-8 py-3" style={{
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.06), inset 0 0 0 1px rgba(0, 0, 0, 0.03), inset -80px 0 60px -50px rgba(0, 0, 0, 0.06), inset 80px 0 60px -50px rgba(0, 0, 0, 0.06)'
    }}>
      {/* Subtle corner gradients */}
      <div className="absolute top-0 left-0 w-40 h-full bg-gradient-to-r from-gray-100 to-transparent opacity-70 pointer-events-none"></div>
      <div className="absolute top-0 right-0 w-40 h-full bg-gradient-to-l from-gray-100 to-transparent opacity-70 pointer-events-none"></div>

      <div className="relative flex items-center justify-center">
        <div className="flex items-center space-x-3">
          {/* Transit icon */}
          <div className="relative">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl flex items-center justify-center border border-blue-100 shadow-sm">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
          </div>

          {/* Title with unique typography */}
          <div>
            <h1 className="text-2xl font-black text-gray-900 tracking-tight" style={{
              fontFamily: "'Inter', system-ui, sans-serif",
              letterSpacing: '-0.03em'
            }}>
              Trans<span className="text-blue-600">i</span>ght
            </h1>
            <p className="text-xs text-gray-500 font-medium tracking-wide" style={{ marginTop: '-2px' }}>
              Toronto Transit Intelligence
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
