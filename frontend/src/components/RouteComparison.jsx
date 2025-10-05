import { useState, useEffect } from 'react';

export default function RouteComparison({ onClose }) {
  const [routes, setRoutes] = useState([null, null, null]);
  const [routeInput, setRouteInput] = useState(['', '', '']);
  const [locationInput, setLocationInput] = useState('');
  const [predictions, setPredictions] = useState([null, null, null]);
  const [loading, setLoading] = useState([false, false, false]);
  const [searchResults, setSearchResults] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);

  // Search for location
  const handleLocationSearch = async (query) => {
    setLocationInput(query);

    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/api/stations/search?query=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSearchResults(data.results || []);
    } catch (error) {
      console.error('Location search error:', error);
    }
  };

  // Select location
  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
    setLocationInput(location.location);
    setSearchResults([]);
  };

  // Add route to comparison
  const handleAddRoute = async (index) => {
    if (!routeInput[index] || !selectedLocation) return;

    const newLoading = [...loading];
    newLoading[index] = true;
    setLoading(newLoading);

    try {
      const response = await fetch(
        `http://localhost:8000/api/stations/${encodeURIComponent(selectedLocation.location)}/predict?route=${routeInput[index]}`
      );
      const data = await response.json();

      const newRoutes = [...routes];
      newRoutes[index] = {
        route: routeInput[index],
        location: selectedLocation.location,
        lat: selectedLocation.lat,
        lon: selectedLocation.lon
      };
      setRoutes(newRoutes);

      const newPredictions = [...predictions];
      newPredictions[index] = data;
      setPredictions(newPredictions);
    } catch (error) {
      console.error('Failed to load predictions:', error);
      alert('Failed to load route predictions');
    } finally {
      const newLoading = [...loading];
      newLoading[index] = false;
      setLoading(newLoading);
    }
  };

  // Remove route from comparison
  const handleRemoveRoute = (index) => {
    const newRoutes = [...routes];
    newRoutes[index] = null;
    setRoutes(newRoutes);

    const newPredictions = [...predictions];
    newPredictions[index] = null;
    setPredictions(newPredictions);

    const newInput = [...routeInput];
    newInput[index] = '';
    setRouteInput(newInput);
  };

  // Get delay color
  const getDelayColor = (delay) => {
    if (delay <= 10) return 'text-green-600 bg-green-50';
    if (delay <= 20) return 'text-yellow-600 bg-yellow-50';
    if (delay <= 30) return 'text-orange-600 bg-orange-50';
    return 'text-red-600 bg-red-50';
  };

  // Get best route index
  const getBestRouteIndex = () => {
    const avgDelays = predictions.map(pred => {
      if (!pred || !pred.predictions) return Infinity;
      const total = pred.predictions.reduce((sum, p) => sum + p.predicted_delay_minutes, 0);
      return total / pred.predictions.length;
    });
    return avgDelays.indexOf(Math.min(...avgDelays));
  };

  const bestIndex = getBestRouteIndex();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-8 py-6 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Compare Routes</h2>
            <p className="text-sm text-gray-600 mt-1">Find the best route for your journey</p>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 rounded-full hover:bg-white flex items-center justify-center transition-colors"
          >
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {/* Location Search */}
          <div className="mb-8">
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Search Station/Location
            </label>
            <div className="relative">
              <input
                type="text"
                value={locationInput}
                onChange={(e) => handleLocationSearch(e.target.value)}
                placeholder="Enter station name or address..."
                className="w-full px-4 py-3 pl-12 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <svg
                className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>

              {/* Search Results Dropdown */}
              {searchResults.length > 0 && (
                <div className="absolute w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-60 overflow-y-auto z-10">
                  {searchResults.map((result, index) => (
                    <button
                      key={index}
                      onClick={() => handleLocationSelect(result)}
                      className="w-full px-4 py-3 text-left hover:bg-blue-50 transition-colors border-b border-gray-100 last:border-b-0"
                    >
                      <p className="text-sm font-medium text-gray-900">{result.location}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {result.lat.toFixed(4)}, {result.lon.toFixed(4)} • Routes: {result.routes.slice(0, 3).join(', ')}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {selectedLocation && (
              <div className="mt-3 px-4 py-2 bg-blue-50 border border-blue-200 rounded-lg flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="text-sm font-medium text-blue-900">{selectedLocation.location}</span>
                </div>
                <button
                  onClick={() => {
                    setSelectedLocation(null);
                    setLocationInput('');
                  }}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Change
                </button>
              </div>
            )}
          </div>

          {/* Route Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[0, 1, 2].map((index) => (
              <div
                key={index}
                className={`border-2 rounded-xl p-6 transition-all ${
                  routes[index]
                    ? bestIndex === index
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 bg-white'
                    : 'border-dashed border-gray-300 bg-gray-50'
                }`}
              >
                {!routes[index] ? (
                  // Empty state - Add route
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3">
                      Route {index + 1}
                    </h3>
                    <input
                      type="text"
                      value={routeInput[index]}
                      onChange={(e) => {
                        const newInput = [...routeInput];
                        newInput[index] = e.target.value;
                        setRouteInput(newInput);
                      }}
                      placeholder="Enter route number..."
                      disabled={!selectedLocation}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                    />
                    <button
                      onClick={() => handleAddRoute(index)}
                      disabled={!routeInput[index] || !selectedLocation || loading[index]}
                      className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium"
                    >
                      {loading[index] ? 'Loading...' : 'Add Route'}
                    </button>
                  </div>
                ) : (
                  // Route comparison card
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-2">
                        <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                          <span className="text-white font-bold text-lg">{routes[index].route}</span>
                        </div>
                        {bestIndex === index && (
                          <div className="px-2 py-1 bg-green-600 text-white text-xs font-bold rounded">
                            BEST
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleRemoveRoute(index)}
                        className="text-gray-400 hover:text-red-600 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>

                    {/* Predictions */}
                    {predictions[index] && predictions[index].predictions && (
                      <div className="space-y-3">
                        <div className="text-center py-3 bg-white rounded-lg border border-gray-200">
                          <p className="text-xs text-gray-600">Average Delay</p>
                          <p className={`text-2xl font-bold mt-1 ${
                            getDelayColor(
                              predictions[index].predictions.reduce((sum, p) => sum + p.predicted_delay_minutes, 0) /
                              predictions[index].predictions.length
                            ).split(' ')[0]
                          }`}>
                            {(
                              predictions[index].predictions.reduce((sum, p) => sum + p.predicted_delay_minutes, 0) /
                              predictions[index].predictions.length
                            ).toFixed(1)} min
                          </p>
                        </div>

                        <div className="space-y-2">
                          <p className="text-xs font-semibold text-gray-700 uppercase">Top Incidents</p>
                          {predictions[index].predictions.slice(0, 3).map((pred, pIndex) => (
                            <div
                              key={pIndex}
                              className={`px-3 py-2 rounded-lg text-xs ${getDelayColor(pred.predicted_delay_minutes)}`}
                            >
                              <div className="flex justify-between items-center">
                                <span className="font-medium truncate">{pred.incident_type}</span>
                                <span className="font-bold ml-2">{pred.predicted_delay_minutes.toFixed(0)} min</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Comparison Summary */}
          {routes.filter(r => r).length >= 2 && (
            <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Recommendation</h3>
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-green-600 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Best Route Right Now</p>
                  <p className="text-xl font-bold text-gray-900">
                    Route {routes[bestIndex]?.route} - Average {(
                      predictions[bestIndex]?.predictions.reduce((sum, p) => sum + p.predicted_delay_minutes, 0) /
                      predictions[bestIndex]?.predictions.length
                    ).toFixed(1)} min delay
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
