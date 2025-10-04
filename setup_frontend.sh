#!/bin/bash

echo "Setting up TTC Delay Prediction Frontend..."

cd /root/Transight/frontend

# Create API client
cat > src/api/api.js << 'EOFAPI'
const API_BASE_URL = 'http://localhost:8000';

export const fetchTimeRange = async () => {
  const response = await fetch(`${API_BASE_URL}/api/time-range`);
  return response.json();
};

export const fetchHistoricalData = async (start, end, minDelay = 5) => {
  const response = await fetch(
    `${API_BASE_URL}/api/historical?start=${start}&end=${end}&min_delay=${minDelay}`
  );
  return response.json();
};

export const fetchPredictions = async (lat, lon, route = '36') => {
  const response = await fetch(
    `${API_BASE_URL}/api/predict?lat=${lat}&lon=${lon}&route=${route}`
  );
  return response.json();
};

export const fetchIncidentTypes = async () => {
  const response = await fetch(`${API_BASE_URL}/api/incident-types`);
  return response.json();
};
EOFAPI

echo "✓ API client created"

# Create Header component
cat > src/components/Header.jsx << 'EOFHEADER'
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
EOFHEADER

echo "✓ Header component created"

# Create TimeSlider component  
cat > src/components/TimeSlider.jsx << 'EOFSLIDER'
import { useState, useEffect } from 'react';
import { format } from 'date-fns';

export default function TimeSlider({ currentTime, timeRange, onChange }) {
  const [sliderValue, setSliderValue] = useState(0);

  useEffect(() => {
    if (timeRange && currentTime) {
      const start = new Date(timeRange.start).getTime();
      const end = new Date(timeRange.end).getTime();
      const current = new Date(currentTime).getTime();
      const percentage = ((current - start) / (end - start)) * 100;
      setSliderValue(percentage);
    }
  }, [currentTime, timeRange]);

  const handleSliderChange = (e) => {
    const percentage = parseFloat(e.target.value);
    setSliderValue(percentage);

    const start = new Date(timeRange.start).getTime();
    const end = new Date(timeRange.end).getTime();
    const timestamp = start + (percentage / 100) * (end - start);

    onChange(new Date(timestamp));
  };

  return (
    <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 bg-white rounded-2xl shadow-soft-lg px-8 py-4 w-[600px] animate-fade-in">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Time Period</span>
          <span className="text-sm font-semibold text-accent">
            {currentTime && format(currentTime, 'MMM d, yyyy HH:mm')}
          </span>
        </div>

        <input
          type="range"
          min="0"
          max="100"
          step="0.1"
          value={sliderValue}
          onChange={handleSliderChange}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-accent"
        />

        <div className="flex justify-between text-xs text-gray-500">
          <span>{timeRange && format(new Date(timeRange.start), 'MMM yyyy')}</span>
          <span>{timeRange && format(new Date(timeRange.end), 'MMM yyyy')}</span>
        </div>
      </div>
    </div>
  );
}
EOFSLIDER

echo "✓ TimeSlider component created"

echo "✅ Frontend setup complete!"
echo "Next steps:"
echo "1. Get a Mapbox token from https://www.mapbox.com/"
echo "2. Add VITE_MAPBOX_TOKEN=your_token to .env file"
echo "3. Run: npm run dev"

