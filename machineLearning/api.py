"""
TTC Delay Prediction FastAPI Server

Provides REST API endpoints for:
1. Historical delay visualization (time-lapse heatmap)
2. Scenario-based predictions (what-if analysis)
"""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uvicorn

from predictor import DelayPredictor

# ============================================================================
# PYDANTIC MODELS (Request/Response schemas)
# ============================================================================

class HistoricalDelayPoint(BaseModel):
    """Single delay incident point for visualization."""
    lat: float
    lon: float
    delay: float
    route: str
    incident: str
    location: str
    datetime: str


class HistoricalTimeSlice(BaseModel):
    """Delays for a single time bin."""
    timestamp: str
    points: List[HistoricalDelayPoint]


class HistoricalDataResponse(BaseModel):
    """Response for historical data endpoint."""
    time_bins: List[HistoricalTimeSlice]
    time_range: dict
    total_incidents: int


class PredictionScenario(BaseModel):
    """Single incident type prediction."""
    incident_type: str
    predicted_delay_minutes: float


class ScenarioPredictionResponse(BaseModel):
    """Response for scenario prediction endpoint."""
    location: dict
    route: str
    timestamp: str
    predictions: List[PredictionScenario]


class ModelMetrics(BaseModel):
    """Model performance metrics."""
    MAE: float
    RMSE: float
    R2: float


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    historical_data_available: bool
    data_records: int
    data_time_range: dict
    model_metrics: ModelMetrics


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="TTC Delay Prediction API",
    description="REST API for TTC bus delay visualization and prediction",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (allow frontend to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global predictor instance (loaded once at startup)
predictor = None


@app.on_event("startup")
async def startup_event():
    """Initialize predictor when server starts."""
    global predictor
    print("\n" + "="*80)
    print("STARTING TTC DELAY PREDICTION API")
    print("="*80)

    try:
        predictor = DelayPredictor()
        print("\n✅ API Ready!")
        print("="*80)
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load predictor: {e}")
        print("Make sure you've run feature_engineering.py first!")
        print("="*80)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "TTC Delay Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "historical": "/api/historical",
            "predict": "/api/predict",
            "time_range": "/api/time-range"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health_check():
    """
    Health check endpoint - verify API and model status.
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    time_range = predictor.get_time_range()

    return {
        "status": "healthy",
        "model_loaded": predictor.model is not None,
        "historical_data_available": predictor.historical_data is not None,
        "data_records": len(predictor.historical_data) if predictor.historical_data is not None else 0,
        "data_time_range": {
            "start": time_range[0].isoformat() if time_range[0] else None,
            "end": time_range[1].isoformat() if time_range[1] else None
        },
        "model_metrics": predictor.metrics
    }


@app.get("/api/time-range", tags=["Historical"])
async def get_time_range():
    """
    Get the available time range of historical data.

    Returns:
        dict: Start and end timestamps of available data
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    start, end = predictor.get_time_range()

    if start is None:
        raise HTTPException(status_code=404, detail="No historical data available")

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "total_days": (end - start).days
    }


@app.get("/api/historical", tags=["Historical"])
async def get_historical_delays(
    start: str = Query(..., description="Start datetime (ISO format: 2024-01-01T00:00:00)"),
    end: str = Query(..., description="End datetime (ISO format: 2024-01-01T23:59:59)"),
    min_delay: float = Query(5.0, description="Minimum delay threshold in minutes"),
    time_bin_hours: int = Query(1, description="Hours per time bin (for aggregation)")
):
    """
    Get historical delay data for time-lapse visualization.

    Args:
        start: Start datetime in ISO format
        end: End datetime in ISO format
        min_delay: Only return delays >= this value (default 5 minutes)
        time_bin_hours: Aggregate delays into time bins (default 1 hour)

    Returns:
        Historical delay data organized by time bins

    Example:
        GET /api/historical?start=2024-01-01T00:00:00&end=2024-01-01T23:59:59
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    try:
        # Get historical delays
        delays = predictor.get_historical_delays(start, end, min_delay_threshold=min_delay)

        if len(delays) == 0:
            return {
                "time_bins": [],
                "time_range": {"start": start, "end": end},
                "total_incidents": 0
            }

        # Add time bins
        import pandas as pd
        delays['time_bin'] = delays['datetime'].dt.floor(f'{time_bin_hours}H')

        # Group by time bin
        time_bins = []
        for time_bin, group in delays.groupby('time_bin'):
            points = [
                {
                    "lat": float(row['latitude']),
                    "lon": float(row['longitude']),
                    "delay": float(row['min_delay']),
                    "route": str(row['route']),
                    "incident": str(row['incident']),
                    "location": str(row['location']),
                    "datetime": row['datetime'].isoformat()
                }
                for _, row in group.iterrows()
            ]

            time_bins.append({
                "timestamp": time_bin.isoformat(),
                "points": points
            })

        return {
            "time_bins": time_bins,
            "time_range": {"start": start, "end": end},
            "total_incidents": len(delays)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving historical data: {str(e)}")


@app.get("/api/historical/heatmap", tags=["Historical"])
async def get_heatmap_grid(
    start: str = Query(..., description="Start datetime"),
    end: str = Query(..., description="End datetime"),
    grid_size: int = Query(50, description="Grid resolution (NxN cells)")
):
    """
    Get historical delays aggregated into spatial grid cells.
    Optimized for heatmap visualization.

    Args:
        start: Start datetime
        end: End datetime
        grid_size: Number of grid cells (creates grid_size x grid_size grid)

    Returns:
        Aggregated delay data by grid cell and time

    Example:
        GET /api/historical/heatmap?start=2024-01-01T00:00:00&end=2024-01-02T00:00:00&grid_size=30
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    try:
        aggregated = predictor.get_hourly_aggregates(start, end, grid_size=grid_size)

        # Convert to JSON-friendly format
        heatmap_data = []
        for _, row in aggregated.iterrows():
            heatmap_data.append({
                "datetime": row['datetime'].isoformat(),
                "lat": float(row['latitude']),
                "lon": float(row['longitude']),
                "avg_delay": float(row['avg_delay']),
                "max_delay": float(row['max_delay']),
                "incident_count": int(row['incident_count'])
            })

        return {
            "heatmap": heatmap_data,
            "grid_size": grid_size,
            "total_cells": len(heatmap_data)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating heatmap: {str(e)}")


@app.get("/api/predict", tags=["Prediction"])
async def predict_scenarios(
    lat: float = Query(..., description="Latitude of location"),
    lon: float = Query(..., description="Longitude of location"),
    route: str = Query("36", description="Bus route number"),
    timestamp: Optional[str] = Query(None, description="Prediction time (ISO format, default: now)")
):
    """
    Predict delays for all possible incident types at a clicked location.

    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        route: Bus route number (default: "36")
        timestamp: Time for prediction (default: current time)

    Returns:
        Predicted delays for all incident scenarios, sorted by severity

    Example:
        GET /api/predict?lat=43.7325&lon=-79.2631&route=36
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    try:
        # Parse timestamp or use current time
        if timestamp:
            prediction_time = datetime.fromisoformat(timestamp)
        else:
            prediction_time = datetime.now()

        # Get predictions for all incident types
        predictions_df = predictor.predict_all_incident_scenarios(
            prediction_time, lat, lon, route
        )

        # Convert to response format
        predictions = [
            {
                "incident_type": row['incident_type'],
                "predicted_delay_minutes": round(row['predicted_delay_minutes'], 1)
            }
            for _, row in predictions_df.iterrows()
        ]

        return {
            "location": {"lat": lat, "lon": lon},
            "route": route,
            "timestamp": prediction_time.isoformat(),
            "predictions": predictions
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.get("/api/predict/single", tags=["Prediction"])
async def predict_single_scenario(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    route: str = Query("36", description="Route number"),
    incident_type: str = Query("Mechanical", description="Incident type"),
    direction: str = Query("NORTH", description="Direction"),
    timestamp: Optional[str] = Query(None, description="Prediction time (default: now)")
):
    """
    Predict delay for a specific incident scenario.

    Args:
        lat: Latitude
        lon: Longitude
        route: Bus route
        incident_type: Type of incident (e.g., "Mechanical", "Collision - TTC")
        direction: Bus direction (NORTH, SOUTH, EAST, WEST, etc.)
        timestamp: Prediction time (default: now)

    Returns:
        Single delay prediction

    Example:
        GET /api/predict/single?lat=43.7325&lon=-79.2631&incident_type=Mechanical
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    try:
        prediction_time = datetime.fromisoformat(timestamp) if timestamp else datetime.now()

        predicted_delay = predictor.predict_delay(
            prediction_time, lat, lon, route, incident_type, direction
        )

        return {
            "location": {"lat": lat, "lon": lon},
            "route": route,
            "incident_type": incident_type,
            "direction": direction,
            "timestamp": prediction_time.isoformat(),
            "predicted_delay_minutes": round(predicted_delay, 1)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.get("/api/incident-types", tags=["Info"])
async def get_incident_types():
    """
    Get list of all available incident types for predictions.

    Returns:
        List of incident type strings
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    if not hasattr(predictor, 'incident_types'):
        return {"incident_types": []}

    return {
        "incident_types": predictor.incident_types,
        "total": len(predictor.incident_types)
    }


@app.get("/api/stations/search", tags=["Search"])
async def search_stations(
    query: str = Query(..., min_length=1, description="Search query for station/location name")
):
    """
    Search for stations/locations with autocomplete suggestions.

    Args:
        query: Search string (minimum 1 character)

    Returns:
        List of matching stations with their coordinates and routes

    Example:
        GET /api/stations/search?query=kennedy
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    if predictor.historical_data is None:
        raise HTTPException(status_code=404, detail="No historical data available")

    try:
        # Get unique locations from historical data
        locations = predictor.historical_data[['location', 'latitude', 'longitude', 'route']].copy()

        # Filter by query (case-insensitive)
        query_lower = query.lower()
        mask = locations['location'].str.lower().str.contains(query_lower, na=False)
        matches = locations[mask]

        # Group by location and aggregate routes
        grouped = matches.groupby(['location', 'latitude', 'longitude']).agg({
            'route': lambda x: sorted([str(r) for r in set(x) if r is not None and str(r) != 'nan'])
        }).reset_index()

        # Limit to top 10 results
        results = []
        for _, row in grouped.head(10).iterrows():
            results.append({
                "location": row['location'],
                "lat": float(row['latitude']),
                "lon": float(row['longitude']),
                "routes": [str(r) for r in row['route']]
            })

        return {
            "query": query,
            "results": results,
            "total": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search error: {str(e)}")


@app.get("/api/stations/{location}/predict", tags=["Search"])
async def get_station_current_prediction(
    location: str = Path(..., description="Station/location name"),
    route: str = Query("36", description="Route number (optional)")
):
    """
    Get current delay predictions for a specific station.

    Args:
        location: Station/location name
        route: Bus route number

    Returns:
        Current delay predictions for all incident scenarios

    Example:
        GET /api/stations/KENNEDY%20STATION/predict?route=36
    """
    if predictor is None:
        raise HTTPException(status_code=503, detail="Predictor not initialized")

    if predictor.historical_data is None:
        raise HTTPException(status_code=404, detail="No historical data available")

    try:
        # Find the station in historical data
        location_data = predictor.historical_data[
            predictor.historical_data['location'].str.upper() == location.upper()
        ]

        if len(location_data) == 0:
            raise HTTPException(status_code=404, detail=f"Location '{location}' not found")

        # Get coordinates (use median to handle slight variations)
        lat = float(location_data['latitude'].median())
        lon = float(location_data['longitude'].median())

        # Get current time
        current_time = datetime.now()

        # Get predictions for all incident types
        predictions_df = predictor.predict_all_incident_scenarios(
            current_time, lat, lon, route
        )

        # Convert to response format
        predictions = [
            {
                "incident_type": row['incident_type'],
                "predicted_delay_minutes": round(row['predicted_delay_minutes'], 1)
            }
            for _, row in predictions_df.iterrows()
        ]

        return {
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "route": route,
            "timestamp": current_time.isoformat(),
            "predictions": predictions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TTC DELAY PREDICTION API SERVER")
    print("="*80)
    print("\nStarting server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Alternative Docs: http://localhost:8000/redoc")
    print("\n" + "="*80 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
