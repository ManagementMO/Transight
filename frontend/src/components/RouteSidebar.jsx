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
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-20 z-40 animate-fade-in"
        onClick={onClose}
      />

      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-soft-lg z-50 animate-slide-in overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900">Route {route.route}</h2>
            <p className="text-sm text-gray-500 mt-1">{route.location}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Current Status */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-600">Current Delay</span>
              <span className={`text-2xl font-bold ${
                route.delay > 20 ? 'text-red-500' : 
                route.delay > 10 ? 'text-yellow-500' : 'text-green-500'
              }`}>
                {route.delay} min
              </span>
            </div>
            <div className="text-xs text-gray-500">
              <p><strong>Incident:</strong> {route.incident}</p>
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

          {/* Prediction Chart */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">
              Predicted Scenarios
            </h3>
            {isLoading ? (
              <div className="flex items-center justify-center h-48">
                <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : chartData.length > 0 ? (
              <DelayChart data={chartData} />
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No prediction data available</p>
            )}
          </div>

          {/* Scenario Predictions */}
          {predictions && predictions.predictions && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Possible Delay Scenarios
              </h3>
              <div className="space-y-2">
                {predictions.predictions.slice(0, 6).map((pred, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <span className="text-sm text-gray-700">{pred.incident_type}</span>
                    <span className={`text-sm font-semibold ${
                      pred.predicted_delay_minutes > 20 ? 'text-red-500' :
                      pred.predicted_delay_minutes > 10 ? 'text-yellow-500' : 'text-green-500'
                    }`}>
                      {pred.predicted_delay_minutes} min
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Common Incidents */}
          <div className="bg-blue-50 rounded-xl p-4">
            <h4 className="text-sm font-semibold text-gray-900 mb-2">Most Common</h4>
            <p className="text-sm text-gray-600">Mechanical issues account for 35% of delays on this route</p>
          </div>
        </div>
      </div>
    </>
  );
}
