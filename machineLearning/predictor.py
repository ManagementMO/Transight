"""
TTC Delay Predictor API
Loads trained model and provides prediction functions for:
1. Historical data retrieval (for time-lapse visualization)
2. Scenario-based predictions (what-if analysis)
"""

import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
MODEL_PATH = os.path.join(SCRIPT_DIR, 'ttc_delay_model.joblib')
HISTORICAL_DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'dataAnalysis', 'geocoded_delays.parquet')

class DelayPredictor:
    """
    Main predictor class that handles both historical data retrieval
    and scenario-based predictions.
    """

    def __init__(self):
        """Initialize by loading model and historical data."""
        print("Loading TTC Delay Predictor...")

        # Load trained model artifacts
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run feature_engineering.py first.")

        artifacts = joblib.load(MODEL_PATH)
        self.model = artifacts['model']
        self.feature_columns = artifacts['feature_columns']
        self.metrics = artifacts['metrics']

        print(f"✓ Model loaded (MAE: {self.metrics['MAE']:.2f} min)")

        # Load historical data for time-series visualization
        if os.path.exists(HISTORICAL_DATA_PATH):
            self.historical_data = pd.read_parquet(HISTORICAL_DATA_PATH)
            self.historical_data['datetime'] = pd.to_datetime(self.historical_data['datetime'])
            print(f"✓ Historical data loaded: {len(self.historical_data):,} records")
        else:
            csv_path = HISTORICAL_DATA_PATH.replace('.parquet', '.csv')
            if os.path.exists(csv_path):
                self.historical_data = pd.read_csv(csv_path)
                self.historical_data['datetime'] = pd.to_datetime(self.historical_data['datetime'])
                print(f"✓ Historical data loaded from CSV: {len(self.historical_data):,} records")
            else:
                self.historical_data = None
                print("⚠ No historical data found. Predictions only mode.")

        # Get unique incident types from historical data
        if self.historical_data is not None:
            self.incident_types = sorted(self.historical_data['incident'].unique())
            print(f"✓ Found {len(self.incident_types)} incident types")

        print("Predictor ready!\n")

    # =========================================================================
    # HISTORICAL DATA RETRIEVAL (for time-lapse visualization)
    # =========================================================================

    def get_historical_delays(self, start_datetime, end_datetime, min_delay_threshold=0):
        """
        Retrieve actual historical delays for visualization.

        Args:
            start_datetime (str or datetime): Start of time range
            end_datetime (str or datetime): End of time range
            min_delay_threshold (float): Only return delays >= this value

        Returns:
            pd.DataFrame: Filtered historical delays with lat/lon for mapping
        """
        if self.historical_data is None:
            raise ValueError("No historical data available")

        start = pd.to_datetime(start_datetime, utc=True).tz_localize(None)
        end = pd.to_datetime(end_datetime, utc=True).tz_localize(None)

        # Ensure datetime column is timezone-naive
        if self.historical_data['datetime'].dt.tz is not None:
            datetime_col = self.historical_data['datetime'].dt.tz_localize(None)
        else:
            datetime_col = self.historical_data['datetime']

        # Filter by time range and minimum delay
        mask = (
            (datetime_col >= start) &
            (datetime_col <= end) &
            (self.historical_data['min_delay'] >= min_delay_threshold)
        )

        filtered = self.historical_data[mask].copy()

        # Return only columns needed for visualization
        viz_columns = [
            'datetime', 'latitude', 'longitude', 'min_delay',
            'route', 'incident', 'location', 'direction'
        ]

        return filtered[viz_columns]

    def get_hourly_aggregates(self, start_datetime, end_datetime, grid_size=50):
        """
        Aggregate delays into hourly time bins and spatial grid cells.
        Useful for smooth time-lapse animation.

        Args:
            start_datetime: Start time
            end_datetime: End time
            grid_size (int): Number of grid cells (creates grid_size x grid_size grid)

        Returns:
            pd.DataFrame: Aggregated delays by hour and grid cell
        """
        if self.historical_data is None:
            raise ValueError("No historical data available")

        delays = self.get_historical_delays(start_datetime, end_datetime)

        # Add hour bin
        delays['hour_bin'] = delays['datetime'].dt.floor('H')

        # Create spatial grid bins
        delays['lat_bin'] = pd.cut(delays['latitude'], bins=grid_size, labels=False)
        delays['lon_bin'] = pd.cut(delays['longitude'], bins=grid_size, labels=False)

        # Aggregate by hour and spatial cell
        aggregated = delays.groupby(['hour_bin', 'lat_bin', 'lon_bin']).agg({
            'min_delay': ['mean', 'max', 'count'],
            'latitude': 'mean',
            'longitude': 'mean'
        }).reset_index()

        # Flatten column names
        aggregated.columns = [
            'datetime', 'lat_bin', 'lon_bin',
            'avg_delay', 'max_delay', 'incident_count',
            'latitude', 'longitude'
        ]

        return aggregated

    def get_time_range(self):
        """Get the available time range of historical data."""
        if self.historical_data is None:
            return None, None

        return (
            self.historical_data['datetime'].min(),
            self.historical_data['datetime'].max()
        )

    # =========================================================================
    # SCENARIO-BASED PREDICTION (what-if analysis)
    # =========================================================================

    def _engineer_prediction_features(self, datetime_obj, latitude, longitude,
                                     route='36', incident_type='Mechanical',
                                     direction='NORTH'):
        """
        Engineer features for a single prediction (mirrors training feature engineering).
        """

        # Initialize feature dict
        features = {}

        # 1. TEMPORAL FEATURES
        features['year'] = datetime_obj.year
        features['month'] = datetime_obj.month
        features['day_of_month'] = datetime_obj.day
        features['day_of_week'] = datetime_obj.weekday()
        features['hour'] = datetime_obj.hour
        features['minute'] = datetime_obj.minute
        features['day_of_year'] = datetime_obj.timetuple().tm_yday
        features['week_of_year'] = datetime_obj.isocalendar()[1]
        features['quarter'] = (datetime_obj.month - 1) // 3 + 1

        # Cyclical encoding
        features['hour_sin'] = np.sin(2 * np.pi * features['hour'] / 24)
        features['hour_cos'] = np.cos(2 * np.pi * features['hour'] / 24)
        features['month_sin'] = np.sin(2 * np.pi * features['month'] / 12)
        features['month_cos'] = np.cos(2 * np.pi * features['month'] / 12)
        features['day_of_week_sin'] = np.sin(2 * np.pi * features['day_of_week'] / 7)
        features['day_of_week_cos'] = np.cos(2 * np.pi * features['day_of_week'] / 7)

        # Boolean flags
        features['is_weekend'] = int(features['day_of_week'] >= 5)
        features['is_rush_hour_am'] = int(7 <= features['hour'] < 10)
        features['is_rush_hour_pm'] = int(16 <= features['hour'] < 19)
        features['is_rush_hour'] = int(features['is_rush_hour_am'] or features['is_rush_hour_pm'])
        features['is_night'] = int(features['hour'] >= 22 or features['hour'] < 6)
        features['is_weekday'] = int(features['day_of_week'] < 5)

        # Season
        season_map = {
            12: 0, 1: 0, 2: 0,  # Winter
            3: 1, 4: 1, 5: 1,   # Spring
            6: 2, 7: 2, 8: 2,   # Summer
            9: 3, 10: 3, 11: 3  # Fall
        }
        features['season'] = season_map[features['month']]

        # 2. SPATIAL FEATURES
        TORONTO_CENTER_LAT = 43.6532
        TORONTO_CENTER_LON = -79.3832

        features['latitude'] = latitude
        features['longitude'] = longitude
        features['dist_from_center'] = np.sqrt(
            (latitude - TORONTO_CENTER_LAT)**2 +
            (longitude - TORONTO_CENTER_LON)**2
        )

        # 3. ROUTE FEATURES
        features['route_numeric'] = float(route) if route.isdigit() else -1
        features['route_is_numeric'] = int(route.isdigit())

        # Route frequency (use historical average)
        if self.historical_data is not None:
            route_freq = self.historical_data['route'].value_counts()
            features['route_frequency'] = route_freq.get(route, route_freq.median())
        else:
            features['route_frequency'] = 100  # Default

        # 4. INCIDENT FEATURES
        # Get average delay for this incident type from historical data
        if self.historical_data is not None:
            incident_avg = self.historical_data.groupby('incident')['min_delay'].mean()
            features['incident_avg_delay'] = incident_avg.get(incident_type, incident_avg.mean())
        else:
            # Rough estimates if no historical data
            incident_estimates = {
                'Mechanical': 20, 'Collision - TTC': 30, 'Emergency Services': 15,
                'Operations - Operator': 10, 'Diversion': 25, 'Investigation': 18
            }
            features['incident_avg_delay'] = incident_estimates.get(incident_type, 15)

        # One-hot encode incident (need to match training columns)
        for col in self.feature_columns:
            if col.startswith('incident_'):
                incident_name = col.replace('incident_', '')
                features[col] = int(incident_type == incident_name or
                                   (incident_name == 'Other' and incident_type not in self.incident_types))

        # 5. DIRECTION FEATURES
        for col in self.feature_columns:
            if col.startswith('dir_'):
                dir_name = col.replace('dir_', '')
                features[col] = int(direction == dir_name)

        # 6. DAY NAME FEATURES
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_name = day_names[features['day_of_week']]
        for col in self.feature_columns:
            if col.startswith('day_'):
                col_day = col.replace('day_', '')
                features[col] = int(day_name == col_day)

        # 7. LOCATION AGGREGATIONS (use historical averages)
        if self.historical_data is not None:
            # Spatial cell average (approximate from nearby historical data)
            nearby = self.historical_data[
                (abs(self.historical_data['latitude'] - latitude) < 0.01) &
                (abs(self.historical_data['longitude'] - longitude) < 0.01)
            ]
            if len(nearby) > 0:
                features['spatial_cell_avg_delay'] = nearby['min_delay'].mean()
                features['location_frequency'] = len(nearby)
            else:
                features['spatial_cell_avg_delay'] = self.historical_data['min_delay'].mean()
                features['location_frequency'] = 10
        else:
            features['spatial_cell_avg_delay'] = 15
            features['location_frequency'] = 10

        # Ensure all model features are present (fill missing with 0)
        for col in self.feature_columns:
            if col not in features:
                features[col] = 0

        # Return features in correct order
        return [features[col] for col in self.feature_columns]

    def predict_delay(self, datetime_obj, latitude, longitude,
                     route='36', incident_type='Mechanical', direction='NORTH'):
        """
        Predict delay for a specific scenario.

        Args:
            datetime_obj (datetime): When the incident occurs
            latitude (float): Location latitude
            longitude (float): Location longitude
            route (str): Bus route number
            incident_type (str): Type of incident
            direction (str): Bus direction

        Returns:
            float: Predicted delay in minutes
        """
        features = self._engineer_prediction_features(
            datetime_obj, latitude, longitude, route, incident_type, direction
        )

        # Convert to DataFrame for prediction
        X = pd.DataFrame([features], columns=self.feature_columns)

        # Predict
        prediction = self.model.predict(X)[0]

        return max(0, prediction)  # Ensure non-negative

    def predict_all_incident_scenarios(self, datetime_obj, latitude, longitude,
                                      route='36', direction='NORTH'):
        """
        Predict delays for ALL possible incident types at a location.
        Useful for "what-if" analysis.

        Returns:
            pd.DataFrame: Predictions for each incident type, sorted by severity
        """
        if self.historical_data is None or not hasattr(self, 'incident_types'):
            # Default incident types if no historical data
            incident_types = [
                'Mechanical', 'Collision - TTC', 'Emergency Services',
                'Operations - Operator', 'Diversion', 'Investigation',
                'Security', 'Cleaning - Unsanitary'
            ]
        else:
            incident_types = self.incident_types

        results = []

        for incident in incident_types:
            try:
                predicted_delay = self.predict_delay(
                    datetime_obj, latitude, longitude, route, incident, direction
                )

                results.append({
                    'incident_type': incident,
                    'predicted_delay_minutes': round(predicted_delay, 1)
                })
            except Exception as e:
                print(f"Warning: Could not predict for {incident}: {e}")
                continue

        # Convert to DataFrame and sort by severity
        df = pd.DataFrame(results).sort_values('predicted_delay_minutes', ascending=False)

        return df


# ============================================================================
# CONVENIENCE FUNCTIONS FOR API/FRONTEND
# ============================================================================

def get_historical_heatmap_data(start_time, end_time, time_bin_hours=1):
    """
    Get historical delay data aggregated for heatmap visualization.

    Args:
        start_time (str): Start datetime (ISO format)
        end_time (str): End datetime (ISO format)
        time_bin_hours (int): Hours per time bin (default 1 hour)

    Returns:
        dict: JSON-serializable heatmap data
    """
    predictor = DelayPredictor()

    delays = predictor.get_historical_delays(start_time, end_time, min_delay_threshold=5)

    # Add time bins
    delays['time_bin'] = delays['datetime'].dt.floor(f'{time_bin_hours}H')

    # Convert to JSON-friendly format
    heatmap_data = []

    for time_bin, group in delays.groupby('time_bin'):
        time_data = {
            'timestamp': time_bin.isoformat(),
            'points': [
                {
                    'lat': row['latitude'],
                    'lon': row['longitude'],
                    'delay': row['min_delay'],
                    'route': row['route'],
                    'incident': row['incident'],
                    'location': row['location']
                }
                for _, row in group.iterrows()
            ]
        }
        heatmap_data.append(time_data)

    return {
        'time_bins': heatmap_data,
        'time_range': {
            'start': start_time,
            'end': end_time
        },
        'total_incidents': len(delays)
    }


def predict_location_scenarios(latitude, longitude, route='36',
                               current_time=None):
    """
    Predict delays for all incident scenarios at a clicked location.

    Args:
        latitude (float): Clicked location lat
        longitude (float): Clicked location lon
        route (str): Bus route
        current_time (str or datetime): Time for prediction (default: now)

    Returns:
        dict: Predictions for all incident types
    """
    predictor = DelayPredictor()

    if current_time is None:
        current_time = datetime.now()
    elif isinstance(current_time, str):
        current_time = pd.to_datetime(current_time)

    predictions = predictor.predict_all_incident_scenarios(
        current_time, latitude, longitude, route
    )

    return {
        'location': {'lat': latitude, 'lon': longitude},
        'route': route,
        'timestamp': current_time.isoformat(),
        'predictions': predictions.to_dict('records')
    }


if __name__ == "__main__":
    # Example usage
    print("\n" + "="*80)
    print("TTC DELAY PREDICTOR - DEMO")
    print("="*80)

    predictor = DelayPredictor()

    # Example 1: Get historical data for visualization
    print("\n1. Historical Data Retrieval:")
    print("-" * 80)
    time_range = predictor.get_time_range()
    if time_range[0]:
        print(f"Available data: {time_range[0]} to {time_range[1]}")

        # Get one day of data
        sample_start = time_range[0]
        sample_end = sample_start + pd.Timedelta(days=1)

        historical = predictor.get_historical_delays(sample_start, sample_end)
        print(f"Sample day delays: {len(historical)} incidents")
        print(f"Average delay: {historical['min_delay'].mean():.1f} minutes")

    # Example 2: Scenario prediction
    print("\n2. Scenario-Based Prediction:")
    print("-" * 80)

    # Predict at Kennedy Station during rush hour
    kennedy_lat, kennedy_lon = 43.7325, -79.2631
    rush_hour_time = datetime(2024, 12, 16, 17, 30)  # Monday 5:30 PM

    print(f"Location: Kennedy Station ({kennedy_lat}, {kennedy_lon})")
    print(f"Time: {rush_hour_time.strftime('%A %I:%M %p')}")
    print(f"Route: 36")
    print("\nPredicted delays for different incident types:\n")

    scenarios = predictor.predict_all_incident_scenarios(
        rush_hour_time, kennedy_lat, kennedy_lon, route='36'
    )

    print(scenarios.to_string(index=False))

    print("\n" + "="*80)
    print("✅ Predictor ready for integration!")
    print("="*80)
