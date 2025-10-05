import { useState, useEffect } from 'react';

export default function LoadingScreen({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    // Simulate loading progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        // Accelerate progress towards the end
        const increment = prev < 70 ? 2 : prev < 90 ? 3 : 5;
        return Math.min(prev + increment, 100);
      });
    }, 50);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (progress === 100) {
      // Wait a bit at 100% before starting fade out
      setTimeout(() => {
        setIsComplete(true);
        // Notify parent after fade animation completes
        setTimeout(() => {
          if (onComplete) onComplete();
        }, 600); // Match the fade-out duration
      }, 300);
    }
  }, [progress, onComplete]);

  return (
    <div
      className={`fixed inset-0 bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center z-50 transition-opacity duration-600 ${
        isComplete ? 'opacity-0' : 'opacity-100'
      }`}
    >
      <div className="text-center">
        {/* Logo */}
        <div className="mb-8 animate-fade-in">
          <div className="relative inline-block">
            <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl flex items-center justify-center shadow-2xl transform hover:scale-105 transition-transform">
              <svg className="w-14 h-14 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
              </svg>
            </div>
            <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-4 border-white animate-pulse"></div>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-4xl font-black text-gray-900 mb-2 tracking-tight" style={{
          fontFamily: "'Inter', system-ui, sans-serif",
          letterSpacing: '-0.03em'
        }}>
          Trans<span className="text-blue-600">i</span>ght
        </h1>
        <p className="text-sm text-gray-500 font-medium mb-12">
          Toronto Transit Intelligence
        </p>

        {/* Progress Bar */}
        <div className="w-80 mx-auto">
          <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden shadow-inner">
            <div
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            >
              {/* Shimmer effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer"></div>
            </div>
          </div>

          {/* Loading text */}
          <div className="mt-4 flex items-center justify-center space-x-2">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm font-medium text-gray-600">
              {progress < 30 ? 'Initializing...' :
               progress < 60 ? 'Loading transit data...' :
               progress < 90 ? 'Preparing map...' :
               progress < 100 ? 'Almost ready...' :
               'Ready!'}
            </span>
          </div>

          {/* Progress percentage */}
          <p className="text-xs text-gray-400 mt-2 font-mono">{progress}%</p>
        </div>
      </div>
    </div>
  );
}
