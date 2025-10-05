const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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

export const searchStations = async (query) => {
  const response = await fetch(`${API_BASE_URL}/api/stations/search?query=${encodeURIComponent(query)}`);
  return response.json();
};

export const fetchStationPredictions = async (location, route) => {
  const response = await fetch(
    `${API_BASE_URL}/api/stations/${encodeURIComponent(location)}/predict?route=${route}`
  );
  return response.json();
};

export const fetchAnalytics = async () => {
  const response = await fetch(`${API_BASE_URL}/api/analytics/overview`);
  return response.json();
};

export { API_BASE_URL };
