export default function Header() {
  return (
    <header className="bg-white border-b border-gray-100 px-8 py-4 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-2 h-2 bg-accent rounded-full animate-pulse"></div>
          <h1 className="text-2xl font-semibold text-gray-900">TTC Delay Insights</h1>
        </div>
        <p className="text-sm text-gray-500">Real-time delay prediction & historical analysis</p>
      </div>
    </header>
  );
}
