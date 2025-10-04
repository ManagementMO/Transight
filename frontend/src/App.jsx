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
        const range = await fetchTimeRange();
        setTimeRange(range);
        // Set initial time to most recent data
        setCurrentTime(new Date(range.end));
      } catch (error) {
        console.error('Failed to load time range:', error);
      }
    };
    loadTimeRange();
  }, []);

  // Load historical data when time changes
  useEffect(() => {
    if (!currentTime) return;

    const loadHistoricalData = async () => {
      setIsLoading(true);
      try {
        // Get 1 hour window of data
        const start = new Date(currentTime);
        const end = new Date(currentTime.getTime() + 60 * 60 * 1000);

        const data = await fetchHistoricalData(
          start.toISOString(),
          end.toISOString(),
          5 // min delay threshold
        );

        setHistoricalData(data);
      } catch (error) {
        console.error('Failed to load historical data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadHistoricalData();
  }, [currentTime]);

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
