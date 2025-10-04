import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';

export default function MapView({ onRouteClick, historicalData, currentTime, isLoading }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize map
  useEffect(() => {
    if (map.current) return; // Initialize map only once

    // Set access token
    mapboxgl.accessToken = import.meta.env.VITE_MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/standard',
      center: [-79.3832, 43.6532], // Toronto coordinates [lng, lat]
      zoom: 11,
      pitch: 45, // Tilt the map for 3D effect
      bearing: 0,
      attributionControl: true
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Wait for style to load before adding layers
    map.current.on('load', () => {
      setMapLoaded(true);
    });

    // Cleanup on unmount
    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
    };
  }, []);

  // Update heatmap when data changes
  useEffect(() => {
    if (!mapLoaded || !historicalData || !map.current) return;

    const points = historicalData.time_bins?.flatMap(bin => bin.points) || [];

    if (points.length === 0) return;

    // Create GeoJSON from delay points
    const geojson = {
      type: 'FeatureCollection',
      features: points.map(point => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [point.lon, point.lat]
        },
        properties: {
          delay: point.delay,
          route: point.route,
          incident: point.incident,
          location: point.location
        }
      }))
    };

    // Remove existing layers and source (proper cleanup order)
    if (map.current.getLayer('delay-points')) {
      map.current.removeLayer('delay-points');
    }
    if (map.current.getLayer('delay-heatmap')) {
      map.current.removeLayer('delay-heatmap');
    }
    if (map.current.getSource('delays')) {
      map.current.removeSource('delays');
    }

    // Add source
    map.current.addSource('delays', {
      type: 'geojson',
      data: geojson
    });

    // Add heatmap layer with vibrant colors
    map.current.addLayer({
      id: 'delay-heatmap',
      type: 'heatmap',
      source: 'delays',
      paint: {
        'heatmap-weight': [
          'interpolate',
          ['linear'],
          ['get', 'delay'],
          0, 0,
          30, 1
        ],
        'heatmap-intensity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 1,
          15, 3
        ],
        'heatmap-color': [
          'interpolate',
          ['linear'],
          ['heatmap-density'],
          0, 'rgba(33, 102, 172, 0)',
          0.2, 'rgb(103, 169, 207)',
          0.4, 'rgb(209, 229, 240)',
          0.6, 'rgb(253, 219, 199)',
          0.8, 'rgb(239, 138, 98)',
          1, 'rgb(178, 24, 43)'
        ],
        'heatmap-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 2,
          15, 30
        ],
        'heatmap-opacity': 0.8
      }
    });

    // Add points layer for interactivity
    map.current.addLayer({
      id: 'delay-points',
      type: 'circle',
      source: 'delays',
      paint: {
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['get', 'delay'],
          0, 4,
          30, 12
        ],
        'circle-color': [
          'interpolate',
          ['linear'],
          ['get', 'delay'],
          0, '#00ff00',
          15, '#ffff00',
          30, '#ff0000'
        ],
        'circle-opacity': 0.8,
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff'
      }
    });

    // Add click handler for delay points
    const clickHandler = (e) => {
      const feature = e.features[0];
      const { route, delay, incident, location } = feature.properties;

      // Create popup with better styling
      new mapboxgl.Popup({
        closeButton: true,
        closeOnClick: false
      })
        .setLngLat(e.lngLat)
        .setHTML(`
          <div style="padding: 12px; font-family: Inter, sans-serif;">
            <h3 style="font-weight: 600; font-size: 16px; margin-bottom: 8px; color: #111827;">Route ${route}</h3>
            <p style="font-size: 13px; color: #6B7280; margin: 4px 0;"><strong>Delay:</strong> ${delay} min</p>
            <p style="font-size: 13px; color: #6B7280; margin: 4px 0;"><strong>Incident:</strong> ${incident}</p>
            <p style="font-size: 13px; color: #6B7280; margin: 4px 0;"><strong>Location:</strong> ${location}</p>
          </div>
        `)
        .addTo(map.current);

      // Trigger route selection callback
      if (onRouteClick) {
        onRouteClick({
          route,
          delay,
          incident,
          location,
          lat: feature.geometry.coordinates[1],
          lon: feature.geometry.coordinates[0]
        });
      }
    };

    map.current.on('click', 'delay-points', clickHandler);

    // Change cursor on hover
    map.current.on('mouseenter', 'delay-points', () => {
      map.current.getCanvas().style.cursor = 'pointer';
    });

    map.current.on('mouseleave', 'delay-points', () => {
      map.current.getCanvas().style.cursor = '';
    });

  }, [mapLoaded, historicalData, onRouteClick]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute top-0 bottom-0 left-0 right-0" />
      
      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-soft px-4 py-2 flex items-center space-x-2">
          <div className="w-2 h-2 bg-accent rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600">Loading data...</span>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-24 right-4 bg-white rounded-lg shadow-soft p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Delay Severity</h4>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-xs text-gray-600">Low (0-10 min)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span className="text-xs text-gray-600">Medium (10-20 min)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-xs text-gray-600">High (20+ min)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
