import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import warnings

warnings.filterwarnings('ignore')

# --- Configuration ---
INPUT_DATA_PATH = 'dataAnalysis/geocoded_delays.parquet' # Use the fast Parquet file
MODEL_OUTPUT_PATH = 'ttc_delay_model_artifacts.joblib'

def load_data(filepath):
    """Loads the dataset from a Parquet file and sets up the datetime column."""
    print(f"--- Loading data from '{filepath}' ---")
    try:
        df = pd.read_parquet(filepath)
    except FileNotFoundError:
        print(f"FATAL ERROR: Data file not found at '{filepath}'.")
        print("Please ensure you've run the data preparation script first.")
        return None
    
    # Ensure datetime is in the correct format
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    print(f"Data loaded successfully. Shape: {df.shape}")
    print(df.info())
    return df

def engineer_features(df):
    """
    Creates a rich set of features from the raw data for the model to learn from.
    This is the most critical step for model accuracy.
    """
    print("\n--- Engineering Features ---")
    
    # Make a copy to avoid modifying the original dataframe
    df_featured = df.copy()

    # 1. Time-Based Features (The most powerful predictors)
    df_featured['hour'] = df_featured['datetime'].dt.hour
    df_featured['day_of_week'] = df_featured['datetime'].dt.dayofweek # Monday=0, Sunday=6
    df_featured['month'] = df_featured['datetime'].dt.month
    df_featured['day_of_year'] = df_featured['datetime'].dt.dayofyear
    df_featured['week_of_year'] = df_featured['datetime'].dt.isocalendar().week.astype(int)

    # 2. Cyclical Features (Helps model understand time's cyclical nature)
    # Hour 23 is as close to hour 0 as hour 1 is. This helps models learn that.
    df_featured['hour_sin'] = np.sin(2 * np.pi * df_featured['hour'] / 24.0)
    df_featured['hour_cos'] = np.cos(2 * np.pi * df_featured['hour'] / 24.0)
    df_featured['month_sin'] = np.sin(2 * np.pi * df_featured['month'] / 12.0)
    df_featured['month_cos'] = np.cos(2 * np.pi * df_featured['month'] / 12.0)

    # 3. Flag/Boolean Features
    df_featured['is_weekend'] = (df_featured['day_of_week'] >= 5).astype(int)
    df_featured['is_rush_hour'] = df_featured['hour'].apply(lambda x: 1 if (7 <= x < 10) or (16 <= x < 19) else 0)

    # 4. Categorical Feature Handling
    # Grouping rare incident types into 'Other' to prevent overfitting
    incident_counts = df_featured['incident'].value_counts(normalize=True)
    rare_incidents = incident_counts[incident_counts < 0.01].index
    df_featured['incident_cleaned'] = df_featured['incident'].replace(rare_incidents, 'Other')
    
    # One-hot encode the cleaned categorical features
    df_featured = pd.get_dummies(df_featured, columns=['incident_cleaned', 'day', 'direction'], 
                                prefix=['inc', 'day', 'dir'])
    
    print("Feature engineering complete. New shape:", df_featured.shape)
    return df_featured

def train_model(df):
    """
    Trains, evaluates, and returns the LightGBM model and the feature columns used.
    """
    print("\n--- Training Model ---")

    # 1. Define Target (y) and Features (X)
    # The target is what we want to predict
    y = df['min_delay'].fillna(0) 

    # The features are all the columns we'll use for prediction
    # CRITICAL: Drop columns that leak information or are not useful
    cols_to_drop = [
        'min_delay', 'min_gap', # 'min_gap' is a result of delay, not a cause (data leakage)
        'datetime', 'vehicle', 'location', 'incident' # Original cols that have been engineered
    ]
    # Also drop original time features that are now encoded cyclically
    cols_to_drop += ['hour', 'month']

    # Ensure all columns to be dropped exist in the dataframe
    cols_to_drop = [col for col in cols_to_drop if col in df.columns]
    
    X = df.drop(columns=cols_to_drop)
    
    # Convert 'route' to numeric, coercing any non-numeric routes to NaN then filling
    X['route'] = pd.to_numeric(X['route'], errors='coerce').fillna(-1)

    # Ensure all columns are numeric for the model
    # This is a safety check
    for col in X.columns:
        if X[col].dtype == 'object':
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

    feature_names = X.columns.tolist()

    # 2. Split Data into Training and Validation Sets
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Training set size: {len(X_train)}, Validation set size: {len(X_val)}")

    # 3. Train the LightGBM Model
    lgbm = lgb.LGBMRegressor(
        objective='regression_l1', # MAE is less sensitive to outliers than MSE
        metric='rmse',
        n_estimators=2000, # High number, will be stopped by early stopping
        learning_rate=0.02,
        num_leaves=60,
        max_depth=10,
        n_jobs=-1,
        seed=42,
        colsample_bytree=0.8, # Use 80% of features for each tree
        subsample=0.8       # Use 80% of data for each tree
    )
    
    print("Starting model training... (this may take a minute or two)")
    lgbm.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric='rmse',
        callbacks=[lgb.early_stopping(100, verbose=True)] # Stop if RMSE doesn't improve for 100 rounds
    )

    # 4. Evaluate the Model
    preds = lgbm.predict(X_val)
    rmse = np.sqrt(mean_squared_error(y_val, preds))
    print("\n--- Model Evaluation ---")
    print(f"Validation RMSE: {rmse:.4f}")
    print(f"This means our model's predictions are, on average, off by about {rmse:.2f} minutes.")
    
    return lgbm, feature_names

def save_artifacts(model, columns, filepath):
    """
    Saves the trained model and the list of feature columns to a single file.
    This is CRITICAL for the backend to use the model correctly.
    """
    print(f"\n--- Saving Model and Artifacts to '{filepath}' ---")
    
    artifacts = {
        'model': model,
        'feature_columns': columns
    }
    
    joblib.dump(artifacts, filepath)
    print("Artifacts saved successfully.")
    print("This file contains everything the backend needs to make predictions.")

if __name__ == "__main__":
    # Execute the entire ML pipeline
    df = load_data(INPUT_DATA_PATH)
    
    if df is not None:
        df_featured = engineer_features(df)
        model, feature_columns = train_model(df_featured)
        save_artifacts(model, feature_columns, MODEL_OUTPUT_PATH)
        print("\n✅ ML Pipeline finished successfully!")