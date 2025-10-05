import { useState, useEffect } from 'react';
import MapView from './components/MapView';
import RouteSidebar from './components/RouteSidebar';
import TimeSlider from './components/TimeSlider';
import Header from './components/Header';
import { fetchHistoricalData, fetchTimeRange } from './api/api';

function App() {
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

  return (
    <div style={{ height: '100vh', width: '100vw' }} className="bg-white flex flex-col overflow-hidden">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        {/* Map */}
        <MapView
          onRouteClick={handleRouteClick}
          historicalData={historicalData}
          isLoading={isLoading}
          onStationSelect={handleStationSelect}
        />

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
      </div>
    </div>
  );
}

export default App;
