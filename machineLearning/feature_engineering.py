import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import warnings
import os

warnings.filterwarnings('ignore')

# --- Configuration ---
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
INPUT_DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'dataAnalysis', 'geocoded_delays.parquet')
MODEL_OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'ttc_delay_model.joblib')
FEATURE_IMPORTANCE_PATH = os.path.join(SCRIPT_DIR, 'feature_importance.csv')

def load_data(filepath):
    """Loads the geocoded delay dataset."""
    print("="*80)
    print("LOADING DATA")
    print("="*80)

    if not os.path.exists(filepath):
        # Try CSV as fallback
        csv_path = filepath.replace('.parquet', '.csv')
        if os.path.exists(csv_path):
            print(f"Parquet not found, loading from CSV: {csv_path}")
            df = pd.read_csv(csv_path)
        else:
            raise FileNotFoundError(f"Data file not found at {filepath} or {csv_path}")
    else:
        print(f"Loading data from: {filepath}")
        df = pd.read_parquet(filepath)

    # Convert datetime
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Sort by datetime for time-series integrity
    df = df.sort_values('datetime').reset_index(drop=True)

    print(f"✓ Loaded {len(df):,} records from {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"  Shape: {df.shape}")

    return df

def engineer_features(df):
    """
    Creates comprehensive features for delay prediction.
    """
    print("\n" + "="*80)
    print("FEATURE ENGINEERING")
    print("="*80)

    df_feat = df.copy()

    # -------------------------------------------------------------------------
    # 1. TEMPORAL FEATURES
    # -------------------------------------------------------------------------
    print("\n1. Creating temporal features...")

    # Basic time components
    df_feat['year'] = df_feat['datetime'].dt.year
    df_feat['month'] = df_feat['datetime'].dt.month
    df_feat['day_of_month'] = df_feat['datetime'].dt.day
    df_feat['day_of_week'] = df_feat['datetime'].dt.dayofweek  # 0=Monday, 6=Sunday
    df_feat['hour'] = df_feat['datetime'].dt.hour
    df_feat['minute'] = df_feat['datetime'].dt.minute
    df_feat['day_of_year'] = df_feat['datetime'].dt.dayofyear
    df_feat['week_of_year'] = df_feat['datetime'].dt.isocalendar().week.astype(int)
    df_feat['quarter'] = df_feat['datetime'].dt.quarter

    # Cyclical encoding (critical for time features)
    df_feat['hour_sin'] = np.sin(2 * np.pi * df_feat['hour'] / 24)
    df_feat['hour_cos'] = np.cos(2 * np.pi * df_feat['hour'] / 24)
    df_feat['month_sin'] = np.sin(2 * np.pi * df_feat['month'] / 12)
    df_feat['month_cos'] = np.cos(2 * np.pi * df_feat['month'] / 12)
    df_feat['day_of_week_sin'] = np.sin(2 * np.pi * df_feat['day_of_week'] / 7)
    df_feat['day_of_week_cos'] = np.cos(2 * np.pi * df_feat['day_of_week'] / 7)

    # Boolean flags
    df_feat['is_weekend'] = (df_feat['day_of_week'] >= 5).astype(int)
    df_feat['is_rush_hour_am'] = ((df_feat['hour'] >= 7) & (df_feat['hour'] < 10)).astype(int)
    df_feat['is_rush_hour_pm'] = ((df_feat['hour'] >= 16) & (df_feat['hour'] < 19)).astype(int)
    df_feat['is_rush_hour'] = (df_feat['is_rush_hour_am'] | df_feat['is_rush_hour_pm']).astype(int)
    df_feat['is_night'] = ((df_feat['hour'] >= 22) | (df_feat['hour'] < 6)).astype(int)
    df_feat['is_weekday'] = (df_feat['day_of_week'] < 5).astype(int)

    # Season
    df_feat['season'] = df_feat['month'].map({
        12: 0, 1: 0, 2: 0,  # Winter
        3: 1, 4: 1, 5: 1,   # Spring
        6: 2, 7: 2, 8: 2,   # Summer
        9: 3, 10: 3, 11: 3  # Fall
    })

    print(f"   Created {15 + 6 + 7 + 1} temporal features")

    # -------------------------------------------------------------------------
    # 2. SPATIAL FEATURES
    # -------------------------------------------------------------------------
    print("\n2. Creating spatial features...")

    # Spatial clustering - identify high-delay zones
    # Distance from city center (approx downtown Toronto)
    TORONTO_CENTER_LAT = 43.6532
    TORONTO_CENTER_LON = -79.3832

    df_feat['dist_from_center'] = np.sqrt(
        (df_feat['latitude'] - TORONTO_CENTER_LAT)**2 +
        (df_feat['longitude'] - TORONTO_CENTER_LON)**2
    )

    # Spatial bins (grid cells)
    df_feat['lat_bin'] = pd.cut(df_feat['latitude'], bins=20, labels=False)
    df_feat['lon_bin'] = pd.cut(df_feat['longitude'], bins=20, labels=False)
    df_feat['spatial_cell'] = df_feat['lat_bin'].astype(str) + '_' + df_feat['lon_bin'].astype(str)

    print(f"   Created 4 spatial features")

    # -------------------------------------------------------------------------
    # 3. ROUTE FEATURES
    # -------------------------------------------------------------------------
    print("\n3. Creating route features...")

    # Convert route to numeric, handle alphanumeric routes
    df_feat['route_numeric'] = pd.to_numeric(df_feat['route'], errors='coerce')
    df_feat['route_is_numeric'] = df_feat['route_numeric'].notna().astype(int)
    df_feat['route_numeric'] = df_feat['route_numeric'].fillna(-1)

    # Route frequency (how busy is this route)
    route_counts = df_feat['route'].value_counts()
    df_feat['route_frequency'] = df_feat['route'].map(route_counts)

    print(f"   Created 3 route features")

    # -------------------------------------------------------------------------
    # 4. INCIDENT TYPE FEATURES
    # -------------------------------------------------------------------------
    print("\n4. Encoding incident types...")

    # Group rare incidents
    incident_counts = df_feat['incident'].value_counts(normalize=True)
    rare_threshold = 0.01
    rare_incidents = incident_counts[incident_counts < rare_threshold].index
    df_feat['incident_grouped'] = df_feat['incident'].replace(rare_incidents, 'Other')

    # REMOVED: Target encoding (was causing data leakage)
    # The model should learn incident severity from patterns, not memorized averages

    # One-hot encode incident types
    incident_dummies = pd.get_dummies(df_feat['incident_grouped'], prefix='incident')
    df_feat = pd.concat([df_feat, incident_dummies], axis=1)

    print(f"   Created {len(incident_dummies.columns)} incident features")

    # -------------------------------------------------------------------------
    # 5. DIRECTION FEATURES
    # -------------------------------------------------------------------------
    print("\n5. Encoding direction...")

    # Fill missing directions
    df_feat['direction'] = df_feat['direction'].fillna('UNKNOWN')

    # Normalize directions
    direction_map = {
        'E': 'EAST', 'W': 'WEST', 'N': 'NORTH', 'S': 'SOUTH',
        'EB': 'EAST', 'WB': 'WEST', 'NB': 'NORTH', 'SB': 'SOUTH',
        'e': 'EAST', 'w': 'WEST', 'n': 'NORTH', 's': 'SOUTH',
        'E/B': 'EAST', 'W/B': 'WEST', 'N/B': 'NORTH', 'S/B': 'SOUTH',
        'BW': 'BIDIRECTIONAL', 'B/W': 'BIDIRECTIONAL', 'both ways': 'BIDIRECTIONAL'
    }
    df_feat['direction_clean'] = df_feat['direction'].replace(direction_map)

    # One-hot encode
    direction_dummies = pd.get_dummies(df_feat['direction_clean'], prefix='dir')
    df_feat = pd.concat([df_feat, direction_dummies], axis=1)

    print(f"   Created {len(direction_dummies.columns)} direction features")

    # -------------------------------------------------------------------------
    # 6. DAY NAME FEATURES
    # -------------------------------------------------------------------------
    print("\n6. Encoding day names...")

    day_dummies = pd.get_dummies(df_feat['day'], prefix='day')
    df_feat = pd.concat([df_feat, day_dummies], axis=1)

    print(f"   Created {len(day_dummies.columns)} day features")

    # -------------------------------------------------------------------------
    # 7. LOCATION-BASED AGGREGATIONS
    # -------------------------------------------------------------------------
    print("\n7. Creating location aggregations...")

    # Average delay by spatial cell
    spatial_avg_delay = df_feat.groupby('spatial_cell')['min_delay'].transform('mean')
    df_feat['spatial_cell_avg_delay'] = spatial_avg_delay

    # Location frequency
    location_counts = df_feat['location'].value_counts()
    df_feat['location_frequency'] = df_feat['location'].map(location_counts)

    print(f"   Created 2 location aggregation features")

    print(f"\n✓ Feature engineering complete: {df_feat.shape[1]} total columns")

    return df_feat

def prepare_training_data(df):
    """
    Prepares X and y for training, handling missing values and selecting features.
    """
    print("\n" + "="*80)
    print("PREPARING TRAINING DATA")
    print("="*80)

    # Target variable
    y = df['min_delay'].fillna(df['min_delay'].median())

    # Drop columns not used for training
    columns_to_drop = [
        'min_delay',        # Target
        'min_gap',          # Leakage (result of delay)
        'datetime',         # Already extracted features
        'location',         # Already extracted features
        'incident',         # Already encoded
        'direction',        # Already encoded
        'route',            # Already encoded
        'day',              # Already encoded
        'vehicle',          # Not predictive
        'incident_grouped', # Intermediate column
        'direction_clean',  # Intermediate column
        'lat_bin',          # Intermediate column
        'lon_bin',          # Intermediate column
        'spatial_cell'      # Categorical, already used for aggregations
    ]

    # Remove columns that exist
    columns_to_drop = [col for col in columns_to_drop if col in df.columns]
    X = df.drop(columns=columns_to_drop)

    # Ensure all features are numeric
    for col in X.columns:
        if X[col].dtype == 'object':
            print(f"   WARNING: Column '{col}' is object type, attempting conversion")
            X[col] = pd.to_numeric(X[col], errors='coerce')

    # Fill any remaining NaNs
    X = X.fillna(0)

    print(f"✓ Training data prepared:")
    print(f"  Features (X): {X.shape}")
    print(f"  Target (y): {y.shape}")
    print(f"  Feature columns: {X.columns.tolist()[:10]}... (+{len(X.columns)-10} more)")

    return X, y

def train_model(X, y):
    """
    Trains LightGBM model with time-series cross-validation.
    """
    print("\n" + "="*80)
    print("MODEL TRAINING")
    print("="*80)

    # Time-series split (respects temporal order)
    tscv = TimeSeriesSplit(n_splits=5)

    print("\nUsing TimeSeriesSplit with 5 folds for validation...")

    # Track metrics across folds
    fold_metrics = []

    # Train final model on all data with best params
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'num_leaves': 63,
        'max_depth': 10,
        'learning_rate': 0.05,
        'n_estimators': 1000,
        'min_child_samples': 20,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'random_state': 42,
        'n_jobs': -1,
        'verbose': -1
    }

    # Validation
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
        print(f"\nFold {fold + 1}/5...")

        X_train_fold, X_val_fold = X.iloc[train_idx], X.iloc[val_idx]
        y_train_fold, y_val_fold = y.iloc[train_idx], y.iloc[val_idx]

        model = lgb.LGBMRegressor(**params)
        model.fit(
            X_train_fold, y_train_fold,
            eval_set=[(X_val_fold, y_val_fold)],
            callbacks=[lgb.early_stopping(50, verbose=False)]
        )

        preds = model.predict(X_val_fold)

        mae = mean_absolute_error(y_val_fold, preds)
        rmse = np.sqrt(mean_squared_error(y_val_fold, preds))
        r2 = r2_score(y_val_fold, preds)

        fold_metrics.append({'fold': fold + 1, 'MAE': mae, 'RMSE': rmse, 'R2': r2})
        print(f"  MAE: {mae:.2f} min | RMSE: {rmse:.2f} min | R²: {r2:.4f}")

    # Print average metrics
    avg_metrics = pd.DataFrame(fold_metrics).mean()
    print("\n" + "="*80)
    print("CROSS-VALIDATION RESULTS")
    print("="*80)
    print(f"Average MAE:  {avg_metrics['MAE']:.2f} minutes")
    print(f"Average RMSE: {avg_metrics['RMSE']:.2f} minutes")
    print(f"Average R²:   {avg_metrics['R2']:.4f}")

    # Train final model on ALL data
    print("\n" + "="*80)
    print("TRAINING FINAL MODEL ON FULL DATASET")
    print("="*80)

    final_model = lgb.LGBMRegressor(**params)
    final_model.fit(X, y)

    print("✓ Final model trained successfully")

    return final_model, avg_metrics

def save_model_artifacts(model, feature_columns, metrics, model_path, importance_path):
    """
    Saves model, feature columns, and feature importance.
    """
    print("\n" + "="*80)
    print("SAVING MODEL ARTIFACTS")
    print("="*80)

    # Save model and metadata
    artifacts = {
        'model': model,
        'feature_columns': feature_columns,
        'metrics': metrics.to_dict(),
        'version': '1.0'
    }

    joblib.dump(artifacts, model_path)
    print(f"✓ Model saved to: {model_path}")

    # Save feature importance
    importance_df = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    importance_df.to_csv(importance_path, index=False)
    print(f"✓ Feature importance saved to: {importance_path}")

    print("\nTop 10 Most Important Features:")
    for idx, row in importance_df.head(10).iterrows():
        print(f"  {row['feature']:30s} {row['importance']:10.0f}")

def main():
    """
    Main ML pipeline execution.
    """
    print("\n" + "="*80)
    print("TTC BUS DELAY PREDICTION - ML PIPELINE")
    print("="*80)

    # 1. Load data
    df = load_data(INPUT_DATA_PATH)

    # 2. Engineer features
    df_featured = engineer_features(df)

    # 3. Prepare training data
    X, y = prepare_training_data(df_featured)

    # 4. Train model
    model, metrics = train_model(X, y)

    # 5. Save artifacts
    save_model_artifacts(
        model,
        X.columns.tolist(),
        metrics,
        MODEL_OUTPUT_PATH,
        FEATURE_IMPORTANCE_PATH
    )

    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETED SUCCESSFULLY")
    print("="*80)
    print(f"\nModel is ready for predictions!")
    print(f"Load with: artifacts = joblib.load('{MODEL_OUTPUT_PATH}')")

if __name__ == "__main__":
    main()
