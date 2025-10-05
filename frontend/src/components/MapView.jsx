import { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import SearchBar from './SearchBar';

export default function MapView({ onRouteClick, historicalData, isLoading, onStationSelect }) {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const currentPopup = useRef(null);
  const hoverPopupRef = useRef(null);
  const justClosedPopup = useRef(false);
  const hoverTimeoutRef = useRef(null);

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
      pitch: 0, // Default birds eye view
      bearing: 0,
      attributionControl: true
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    // Wait for style to load before adding layers
    map.current.on('load', () => {
      setMapLoaded(true);
    });

    // Listen for sidebar close event
    const handleSidebarClose = () => {
      justClosedPopup.current = true;

      // Remove any hover popup
      if (hoverPopupRef.current) {
        hoverPopupRef.current.remove();
        hoverPopupRef.current = null;
      }

      // Reset flag after a longer delay to ensure user has moved mouse
      setTimeout(() => {
        justClosedPopup.current = false;
      }, 500);
    };

    window.addEventListener('sidebarClosed', handleSidebarClose);

    // Cleanup on unmount
    return () => {
      window.removeEventListener('sidebarClosed', handleSidebarClose);
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

    // Smooth fade-out animation before updating
    const fadeOutLayers = () => {
      if (map.current.getLayer('delay-points')) {
        map.current.setPaintProperty('delay-points', 'circle-opacity', 0);
      }
      if (map.current.getLayer('delay-heatmap')) {
        map.current.setPaintProperty('delay-heatmap', 'heatmap-opacity', 0);
      }
    };

    // Fade out existing layers
    fadeOutLayers();

    // Wait for fade animation, then update layers
    setTimeout(() => {
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

    // Add heatmap layer with vibrant colors and transitions
    map.current.addLayer({
      id: 'delay-heatmap',
      type: 'heatmap',
      source: 'delays',
      paint: {
        'heatmap-opacity-transition': {duration: 500},
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
          0, 0.8,
          15, 2.5
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
          0, 4,
          15, 40
        ],
        'heatmap-opacity': 0.8
      }
    });

    // Add points layer for interactivity with vibrant colors and transitions
    map.current.addLayer({
      id: 'delay-points',
      type: 'circle',
      source: 'delays',
      paint: {
        'circle-opacity-transition': {duration: 500},
        'circle-stroke-opacity-transition': {duration: 500},
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          8, [
            'interpolate',
            ['linear'],
            ['get', 'delay'],
            0, 3,
            15, 6,
            30, 10
          ],
          14, [
            'interpolate',
            ['linear'],
            ['get', 'delay'],
            0, 6,
            15, 10,
            30, 16
          ]
        ],
        'circle-color': [
          'interpolate',
          ['linear'],
          ['get', 'delay'],
          0, '#10b981',   // Vibrant green for low delays
          10, '#fbbf24',  // Vibrant yellow for medium delays
          20, '#f97316',  // Vibrant orange for high delays
          30, '#dc2626'   // Vibrant red for severe delays
        ],
        'circle-opacity': 0, // Start invisible for fade-in
        'circle-stroke-width': 2,
        'circle-stroke-color': '#ffffff',
        'circle-stroke-opacity': 0 // Start invisible for fade-in
      }
    });

      // Smooth fade-in animation
      setTimeout(() => {
        if (map.current.getLayer('delay-heatmap')) {
          map.current.setPaintProperty('delay-heatmap', 'heatmap-opacity', 0.8);
        }
        if (map.current.getLayer('delay-points')) {
          map.current.setPaintProperty('delay-points', 'circle-opacity', 0.9);
          map.current.setPaintProperty('delay-points', 'circle-stroke-opacity', 1);
        }
      }, 50);

    }, 300); // Wait for fade-out before rebuilding layers

    // Add click handler for delay points
    const clickHandler = (e) => {
      const feature = e.features[0];
      const { route, delay, incident, location } = feature.properties;

      // Clear any existing timeout
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
        hoverTimeoutRef.current = null;
      }

      // Set flag to prevent hover popup from appearing
      justClosedPopup.current = true;

      // Remove hover popup when clicking
      if (hoverPopupRef.current) {
        hoverPopupRef.current.remove();
        hoverPopupRef.current = null;
      }

      // Close existing click popup if any
      if (currentPopup.current) {
        currentPopup.current.remove();
      }

      // Reset the flag after delay to allow hover again
      hoverTimeoutRef.current = setTimeout(() => {
        justClosedPopup.current = false;
        hoverTimeoutRef.current = null;
      }, 1000);

      // Create popup with better styling
      const popup = new mapboxgl.Popup({
        closeButton: true,
        closeOnClick: false,
        className: 'delay-popup'
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

      // Store current popup reference
      currentPopup.current = popup;

      // Clean up reference and hover popup when popup is closed
      popup.on('close', () => {
        currentPopup.current = null;
        justClosedPopup.current = true;

        // Also remove any lingering hover popup
        if (hoverPopupRef.current) {
          hoverPopupRef.current.remove();
          hoverPopupRef.current = null;
        }

        // Reset the flag after a longer delay
        setTimeout(() => {
          justClosedPopup.current = false;
        }, 500);
      });

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

    // Hover popup for delay points
    map.current.on('mouseenter', 'delay-points', (e) => {
      // Change cursor
      map.current.getCanvas().style.cursor = 'pointer';

      // Don't show hover popup if click popup is open OR just closed
      if (currentPopup.current || justClosedPopup.current) {
        return;
      }

      // Remove existing hover popup if any
      if (hoverPopupRef.current) {
        hoverPopupRef.current.remove();
        hoverPopupRef.current = null;
      }

      // Get feature data
      const feature = e.features[0];
      const { route, delay, incident, location } = feature.properties;
      const coordinates = feature.geometry.coordinates.slice();

      // Create hover popup - positioned with arrow pointing to the point
      const hoverPopup = new mapboxgl.Popup({
        closeButton: false,
        closeOnClick: false,
        className: 'delay-popup-hover',
        anchor: 'bottom',  // Arrow points down to the point
        offset: [0, -15]   // Offset upward from the point
      })
        .setLngLat(coordinates)
        .setHTML(`
          <div style="padding: 10px; font-family: Inter, sans-serif;">
            <h3 style="font-weight: 600; font-size: 14px; margin-bottom: 6px; color: #111827;">Route ${route}</h3>
            <p style="font-size: 12px; color: #6B7280; margin: 3px 0;"><strong>Delay:</strong> ${delay} min</p>
            <p style="font-size: 12px; color: #6B7280; margin: 3px 0;"><strong>Incident:</strong> ${incident}</p>
            <p style="font-size: 12px; color: #6B7280; margin: 3px 0; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;"><strong>Location:</strong> ${location}</p>
          </div>
        `)
        .addTo(map.current);

      // Store in ref
      hoverPopupRef.current = hoverPopup;
    });

    map.current.on('mouseleave', 'delay-points', () => {
      map.current.getCanvas().style.cursor = '';

      // Remove hover popup
      if (hoverPopupRef.current) {
        hoverPopupRef.current.remove();
        hoverPopupRef.current = null;
      }
    });

  }, [mapLoaded, historicalData, onRouteClick]);

  return (
    <div className="relative w-full h-full">
      <div ref={mapContainer} className="absolute top-0 bottom-0 left-0 right-0" />

      {/* Search Bar - Top Right */}
      <div className="absolute top-4 right-16 z-10">
        <SearchBar onStationSelect={onStationSelect} />
      </div>

      {/* Loading indicator */}
      {isLoading && (
        <div className="absolute top-4 left-4 bg-white rounded-xl shadow-soft-lg px-5 py-3 flex items-center space-x-3 animate-fade-in border border-blue-100 z-10">
          <div className="relative">
            <div className="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
            <div className="absolute inset-0 w-3 h-3 bg-blue-400 rounded-full animate-ping"></div>
          </div>
          <span className="text-sm text-gray-700 font-medium">Updating timeline...</span>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-24 right-4 bg-white rounded-xl shadow-soft-lg p-5" style={{ backdropFilter: 'blur(10px)', backgroundColor: 'rgba(255, 255, 255, 0.95)' }}>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Delay Severity</h4>
        <div className="space-y-2">
          <div className="flex items-center space-x-3">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#10b981' }}></div>
            <span className="text-xs text-gray-700 font-medium">Low (0-10 min)</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#fbbf24' }}></div>
            <span className="text-xs text-gray-700 font-medium">Medium (10-20 min)</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#f97316' }}></div>
            <span className="text-xs text-gray-700 font-medium">High (20-30 min)</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#dc2626' }}></div>
            <span className="text-xs text-gray-700 font-medium">Severe (30+ min)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
