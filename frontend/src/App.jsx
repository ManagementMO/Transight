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
        // Get 12 hour window of data to show many more incidents
        const start = new Date(currentTime.getTime() - 6 * 60 * 60 * 1000); // 6 hours before
        const end = new Date(currentTime.getTime() + 6 * 60 * 60 * 1000); // 6 hours after

        console.log('📡 Fetching historical data:', {
          start: start.toISOString(),
          end: end.toISOString()
        });

        const data = await fetchHistoricalData(
          start.toISOString(),
          end.toISOString(),
          2 // min delay threshold (reduced to show even more incidents)
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
          currentTime={currentTime}
          isLoading={isLoading}
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
