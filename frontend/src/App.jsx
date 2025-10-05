import { useState, useEffect } from 'react';
import MapView from './components/MapView';
import RouteSidebar from './components/RouteSidebar';
import TimeSlider from './components/TimeSlider';
import Header from './components/Header';
import Analytics from './components/Analytics';
import LoadingScreen from './components/LoadingScreen';
import { fetchHistoricalData, fetchTimeRange } from './api/api';

function App() {
  const [showLoading, setShowLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('map'); // 'map' or 'analytics'
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [timeRange, setTimeRange] = useState(null);
  const [historicalData, setHistoricalData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load available time range on mount
  useEffect(() => {
    const loadTimeRange = async () => {
      try {
        console.log('📡 Fetching time range...');
        const range = await fetchTimeRange();
        console.log('✅ Time range loaded:', range);
        setTimeRange(range);
        // Set initial time to most recent data
        setCurrentTime(new Date(range.end));
      } catch (error) {
        console.error('❌ Failed to load time range:', error);
      }
    };
    loadTimeRange();
  }, []);

  // Load historical data when time changes
  useEffect(() => {
    if (!currentTime || !timeRange) return;

    const loadHistoricalData = async () => {
      setIsLoading(true);
      try {
        // Get 24 hour window of data to show maximum incidents across Toronto
        const start = new Date(currentTime.getTime() - 12 * 60 * 60 * 1000); // 12 hours before
        const end = new Date(currentTime.getTime() + 12 * 60 * 60 * 1000); // 12 hours after

        console.log('📡 Fetching historical data:', {
          start: start.toISOString(),
          end: end.toISOString()
        });

        const data = await fetchHistoricalData(
          start.toISOString(),
          end.toISOString(),
          0 // Show ALL delays (even 0 min delays to maximize hotspots)
        );

        console.log('✅ Historical data loaded:', data.total_incidents, 'incidents');
        setHistoricalData(data);
      } catch (error) {
        console.error('❌ Failed to load historical data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadHistoricalData();
  }, [currentTime, timeRange]);

  const handleRouteClick = (route) => {
    setSelectedRoute(route);
  };

  const handleCloseSidebar = () => {
    setSelectedRoute(null);

    // Trigger a custom event to notify map that sidebar was closed
    window.dispatchEvent(new CustomEvent('sidebarClosed'));
  };

  const handleStationSelect = (stationData) => {
    // When user searches for a station, show it in the sidebar
    setSelectedRoute({
      route: stationData.routes[0] || 'Multiple',
      lat: stationData.lat,
      lon: stationData.lon,
      location: stationData.location,
      delay: stationData.predictions?.[0]?.predicted_delay_minutes || 0,
      incident: stationData.predictions?.[0]?.incident_type || 'Current Prediction',
      predictions: stationData.predictions,
      timestamp: stationData.timestamp
    });
  };

  const handleExportCSV = () => {
    if (!historicalData || !historicalData.time_bins) {
      alert('No data available to export');
      return;
    }

    // Flatten all points from time bins
    const points = historicalData.time_bins.flatMap(bin => bin.points);

    if (points.length === 0) {
      alert('No data points to export');
      return;
    }

    // CSV headers
    const headers = ['Timestamp', 'Route', 'Delay (min)', 'Incident Type', 'Location', 'Latitude', 'Longitude'];

    // CSV rows
    const rows = points.map(point => [
      currentTime.toISOString(),
      point.route,
      point.delay,
      point.incident,
      point.location,
      point.lat,
      point.lon
    ]);

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `transight-delays-${currentTime.toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      {/* Loading Screen */}
      {showLoading && <LoadingScreen onComplete={() => setShowLoading(false)} />}

      {/* Main App */}
      <div style={{ height: '100vh', width: '100vw' }} className="bg-white flex flex-col overflow-hidden">
        {/* Header */}
        <Header />

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 bg-white px-8">
        <div className="flex space-x-1">
          <button
            onClick={() => setActiveTab('map')}
            className={`px-6 py-3 text-sm font-semibold transition-all relative ${
              activeTab === 'map'
                ? 'text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Map View
            {activeTab === 'map' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"></div>
            )}
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-6 py-3 text-sm font-semibold transition-all relative ${
              activeTab === 'analytics'
                ? 'text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Analytics Dashboard
            {activeTab === 'analytics' && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600"></div>
            )}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        {activeTab === 'map' ? (
          <>
            {/* Map */}
            <MapView
              onRouteClick={handleRouteClick}
              historicalData={historicalData}
              isLoading={isLoading}
              onStationSelect={handleStationSelect}
            />

            {/* Export CSV Button */}
            <button
              onClick={handleExportCSV}
              className="absolute top-4 left-4 bg-white rounded-xl shadow-soft-lg px-4 py-2 flex items-center space-x-2 hover:bg-gray-50 transition-colors border border-gray-200 z-10"
            >
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="text-sm font-medium text-gray-700">Export CSV</span>
            </button>

            {/* Time Slider */}
            {timeRange && (
              <TimeSlider
                currentTime={currentTime}
                timeRange={timeRange}
                onChange={setCurrentTime}
              />
            )}

            {/* Route Sidebar */}
            {selectedRoute && (
              <RouteSidebar
                route={selectedRoute}
                onClose={handleCloseSidebar}
              />
            )}
          </>
        ) : (
          <Analytics />
        )}
      </div>
      </div>
    </>
  );
}

export default App;
