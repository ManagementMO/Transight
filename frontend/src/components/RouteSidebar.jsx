import { useState, useEffect } from 'react';
import DelayChart from './DelayChart';
import { fetchPredictions } from '../api/api';

export default function RouteSidebar({ route, onClose }) {
  const [predictions, setPredictions] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadPredictions = async () => {
      setIsLoading(true);
      try {
        const data = await fetchPredictions(route.lat, route.lon, route.route);
        setPredictions(data);
      } catch (error) {
        console.error('Failed to load predictions:', error);
      } finally {
        setIsLoading(false);
      }
    };

    if (route) {
      loadPredictions();
    }
  }, [route]);

  // Generate mock 3-hour prediction data for chart
  const chartData = predictions?.predictions?.slice(0, 5).map((p, i) => ({
    time: `${new Date().getHours() + i}:00`,
    delay: p.predicted_delay_minutes
  })) || [];

  return (
    <>
      {/* Backdrop with blur */}
      <div
        className="fixed inset-0 bg-black bg-opacity-40 z-40 animate-fade-in"
        style={{backdropFilter: 'blur(8px)'}}
        onClick={onClose}
      />

      {/* Center Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in pointer-events-none">
        <div
          className="bg-white rounded-3xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden pointer-events-auto animate-scale-in"
          style={{
            animation: 'scaleIn 0.3s ease-out',
            transformOrigin: 'center'
          }}
        >
          <div className="overflow-y-auto max-h-[90vh]">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-8 py-6 flex items-center justify-between z-10" style={{backdropFilter: 'blur(10px)', backgroundColor: 'rgba(255, 255, 255, 0.98)'}}>
          <div className="flex-1 min-w-0">
            <h2 className="text-3xl font-bold text-gray-900">Route {route.route}</h2>
            <p className="text-sm text-gray-600 mt-2 truncate">{route.location}</p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-3 bg-gray-100 hover:bg-gray-200 rounded-full transition-all hover:scale-110 flex-shrink-0 shadow-md hover:shadow-lg"
            aria-label="Close"
          >
            <svg className="w-6 h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-8 space-y-8 pb-24">
          {/* Current Status - Hero Card */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-semibold text-blue-900 uppercase tracking-wide">Current Delay</span>
              <div className={`px-4 py-2 rounded-full font-bold text-white ${
                route.delay > 20 ? 'bg-red-500' :
                route.delay > 10 ? 'bg-yellow-500' : 'bg-green-500'
              }`}>
                <span className="text-3xl">{route.delay}</span>
                <span className="text-lg ml-1">min</span>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-blue-200">
              <p className="text-sm text-blue-900 font-medium mb-1">Incident Type</p>
              <p className="text-base text-blue-800">{route.incident}</p>
            </div>
          </div>

          {/* Key Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white border border-gray-100 rounded-xl p-4">
              <p className="text-xs text-gray-500 mb-1">Avg This Month</p>
              <p className="text-2xl font-bold text-gray-900">12.5 min</p>
            </div>
            <div className="bg-white border border-gray-100 rounded-xl p-4">
              <p className="text-xs text-gray-500 mb-1">Incidents Today</p>
              <p className="text-2xl font-bold text-gray-900">8</p>
            </div>
          </div>

          {/* Prediction Chart - Featured Section */}
          <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-3xl border-2 border-blue-200 p-8 shadow-lg">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900 flex items-center">
                <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center mr-3">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                Delay Forecast
              </h3>
              <span className="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full uppercase tracking-wide">Live</span>
            </div>
            {isLoading ? (
              <div className="flex flex-col items-center justify-center h-64 bg-white bg-opacity-50 rounded-2xl">
                <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-sm text-gray-600 font-medium">Loading predictions...</p>
              </div>
            ) : chartData.length > 0 ? (
              <div className="bg-white bg-opacity-80 rounded-2xl p-6 backdrop-blur-sm">
                <DelayChart data={chartData} />
              </div>
            ) : (
              <div className="text-center py-16 bg-white bg-opacity-50 rounded-2xl">
                <svg className="w-20 h-20 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-base text-gray-600 font-medium">No prediction data available</p>
                <p className="text-sm text-gray-500 mt-2">Check back soon for updates</p>
              </div>
            )}
          </div>

          {/* Scenario Predictions */}
          {predictions && predictions.predictions && (
            <div className="bg-white rounded-2xl border border-gray-200 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center">
                <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                What-If Scenarios
              </h3>
              <div className="space-y-3">
                {predictions.predictions.slice(0, 8).map((pred, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-gray-100 rounded-xl hover:shadow-md transition-all border border-gray-200 hover:border-blue-200"
                  >
                    <div className="flex-1 min-w-0 mr-4">
                      <span className="text-sm font-medium text-gray-900 block truncate">{pred.incident_type}</span>
                      <span className="text-xs text-gray-500 mt-1 block">Predicted impact</span>
                    </div>
                    <div className={`px-3 py-2 rounded-lg font-bold text-white flex-shrink-0 ${
                      pred.predicted_delay_minutes > 20 ? 'bg-red-500' :
                      pred.predicted_delay_minutes > 10 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}>
                      {pred.predicted_delay_minutes.toFixed(1)} min
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Common Incidents */}
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-100">
            <h4 className="text-sm font-bold text-blue-900 mb-2 uppercase tracking-wide">💡 Insight</h4>
            <p className="text-sm text-blue-800 font-medium">Mechanical issues account for 35% of delays on this route</p>
          </div>
        </div>
          </div>
        </div>
      </div>
    </>
  );
}
