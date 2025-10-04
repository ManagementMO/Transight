import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

print("Starting model training process...")

# --- Step 1: Data Loading and Initial Preparation ---
df = pd.read_parquet('dataAnalysis/geocoded_delays.parquet')
df['datetime'] = pd.to_datetime(df['datetime'])
df['min_delay'] = df['min_delay'].fillna(0)

# --- Step 2: Pre-Aggregation Feature Engineering ---

# 2a. Create time-based features from the raw data
df['day_of_week'] = df['datetime'].dt.dayofweek # Monday=0, Sunday=6
df['month'] = df['datetime'].dt.month

interval = 15

# --- MODIFICATION: Create a 30-minute time bucket for grouping ---
df['time_bucket'] = df['datetime'].dt.floor(f'{interval}T')

# 2b. Clean up direction and other categorical features
dir_map = {'E': 'E', 'EB': 'E', 'W': 'W', 'WB': 'W', 'N': 'N', 'NB': 'N', 'S': 'S', 'SB': 'S'}
df['direction_cleaned'] = df['direction'].str.upper().map(dir_map).fillna('Other')

# 2c. One-Hot Encode categorical variables BEFORE aggregation
df = pd.get_dummies(df, columns=['incident', 'direction_cleaned', 'day'], prefix=['inc', 'dir', 'day'])

# --- Step 3: Data Aggregation to 30-Minute Level ---
# --- MODIFICATION: We now group by the 'time_bucket' instead of 'date' and 'hour' ---
grouping_keys = ['route', 'latitude', 'longitude', 'time_bucket', 'day_of_week', 'month']

# Define how to aggregate each column
aggregation_rules = {
    'min_delay': 'mean' # The new target: average delay in this 30-min interval
}

# Add rules for all the one-hot encoded columns: we sum them up
for col in df.columns:
    if col.startswith(('inc_', 'dir_', 'day_')):
        aggregation_rules[col] = 'sum'

# --- MODIFICATION: Updated print statement ---
print("Aggregating data to "f'{interval}-minute intervals...')
df_agg = df.groupby(grouping_keys, as_index=False).agg(aggregation_rules)

# --- Step 4: Post-Aggregation Feature Engineering (Cyclic Features) ---
print("Creating cyclic time features...")

# --- MODIFICATION: Create more granular cyclic features for 30-minute intervals ---
# First, extract hour and minute from the time_bucket
df_agg['hour'] = df_agg['time_bucket'].dt.hour
df_agg['minute'] = df_agg['time_bucket'].dt.minute

# There are 48 thirty-minute intervals in a day (24 * 2)
# Calculate the interval number (0-47) for each row
total_intervals_in_day = 24 * 60/interval
current_interval = df_agg['hour'] * 60/interval + (df_agg['minute'] / interval)

# Create sine/cosine features based on this 0-47 interval number
df_agg['interval_sin'] = np.sin(2 * np.pi * current_interval / total_intervals_in_day)
df_agg['interval_cos'] = np.cos(2 * np.pi * current_interval / total_intervals_in_day)

# The Day of Week cyclic features remain the same
df_agg['day_of_week_sin'] = np.sin(2 * np.pi * df_agg['day_of_week'] / 7.0)
df_agg['day_of_week_cos'] = np.cos(2 * np.pi * df_agg['day_of_week'] / 7.0)


# --- Step 4.5: One-Hot Encode Remaining Categorical Features ---
print("One-hot encoding the 'route' column...")
df_agg = pd.get_dummies(df_agg, columns=['route'], prefix='rt')


# --- Step 5: Final Feature and Target Selection ---
y = df_agg['min_delay']

# --- MODIFICATION: Update the list of columns to drop ---
# We drop the new time bucket and intermediate time columns.
feature_columns_to_drop = ['min_delay', 'time_bucket', 'hour', 'minute', 'day_of_week']
X = df_agg.drop(columns=feature_columns_to_drop)

# Keep the list of final columns for the backend
final_feature_columns = X.columns.tolist()
print(f"Dataset prepared with {len(df_agg)} aggregated rows and {len(final_feature_columns)} features.")


# --- Step 6: Advanced Train-Test Split ---
print("\nPerforming advanced train-test split...")

# --- MODIFICATION: Use 'time_bucket' to filter by year instead of 'date' ---
# 1. Isolate the two main pools of data
historical_data = df_agg[df_agg['time_bucket'].dt.year < 2022]
recent_data = df_agg[df_agg['time_bucket'].dt.year >= 2022]

print(f"Identified {len(historical_data)} rows of historical data (before 2022).")
print(f"Identified {len(recent_data)} rows of recent data (2022-2024).")

# Use a 80/20 split for the recent data
test_size_factor = 0.25

# 2. Split the 'recent_data' pool
recent_train, test_set = train_test_split(
    recent_data,
    test_size=test_size_factor,
    random_state=42
)

# 3. Create the final, complete training set
train_set = pd.concat([historical_data, recent_train], ignore_index=True)

# 4. Separate the final dataframes into features (X) and target (y)
y_train = train_set['min_delay']
X_train = train_set.drop(columns=feature_columns_to_drop)

y_test = test_set['min_delay']
X_test = test_set.drop(columns=feature_columns_to_drop)

# --- Sanity Check and Final Report ---
print(f"\nFinal training set contains {len(X_train)} samples.")
print(f" -> Includes all {len(historical_data)} historical rows.")
print(f" -> Includes {len(recent_train)} ({int(100 - test_size_factor*100)}%) of recent rows.")
print(f"Final testing set contains {len(X_test)} samples ({int(test_size_factor*100)}% of recent rows).")


# --- Final Column Alignment (Safety Check) ---
train_cols = X_train.columns
test_cols = X_test.columns

missing_in_test = set(train_cols) - set(test_cols)
for c in missing_in_test:
    X_test[c] = 0

missing_in_train = set(test_cols) - set(train_cols)
for c in missing_in_train:
    X_train[c] = 0

X_test = X_test[train_cols]

# --- Step 7: Model Training with LightGBM ---
print("\nTraining LightGBM model...")

lgbm = lgb.LGBMRegressor(
    objective='regression_l1',
    n_estimators=1000,
    learning_rate=0.05,
    num_leaves=40,
    max_depth=10,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1
)

lgbm.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    eval_metric='l1',
    callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=True)]
)

# --- Step 8: Evaluation and Saving ---
print("\nEvaluating model on the test set...")
predictions = lgbm.predict(X_test)
mae = mean_absolute_error(y_test, predictions)

print(f"\n========================================================")
print(f" Model Performance: Mean Absolute Error = {mae:.2f} minutes")
print(f" This means, on average, the model's prediction is off by {mae:.2f} minutes.")
print(f"========================================================")

# --- SUGGESTION: Save the new model and columns with a different name ---
joblib.dump(lgbm, 'ttc_delay_model_30min.joblib')
joblib.dump(final_feature_columns, 'model_feature_columns_30min.joblib')

print("\nModel and feature columns saved successfully!")
print("Ready for the backend.")