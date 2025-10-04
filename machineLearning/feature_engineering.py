import pandas as pd
import joblib

df = pd.read_parquet('dataAnalysis/geocoded_delays.parquet')
print(df.head())

df['datetime'] = pd.to_datetime(df['datetime'])

# 1. Extract from datetime
df['hour'] = df['datetime'].dt.hour
df['day_of_week'] = df['datetime'].dt.dayofweek
df['month'] = df['datetime'].dt.month
df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)

# 2. Clean up categorical features
# Standardize direction codes
dir_map = {'E': 'E', 'EB': 'E', 'W': 'W', 'WB': 'W', 'N': 'N', 'NB': 'N', 'S': 'S', 'SB': 'S'}
df['direction_cleaned'] = df['direction'].str.upper().map(dir_map).fillna('Other')

# 3. One-Hot Encode
# Convert text columns into numerical format
df = pd.get_dummies(df, columns=['incident', 'direction_cleaned', 'day'], prefix=['inc', 'dir', 'day'])

# The target is what you want to predict
y = df['min_delay'].fillna(0) # Fill any missing delays with 0

# The features are the data we use to make the prediction
# CRITICAL: Do NOT include 'min_gap', 'vehicle', 'location', or 'datetime'
# 'min_gap' leaks information about the answer. 'vehicle' is just noise.
feature_columns = [col for col in df.columns if col.startswith(('inc_', 'dir_', 'day_'))]
feature_columns += ['route', 'hour', 'day_of_week', 'month', 'is_weekend', 'latitude', 'longitude']

X = df[feature_columns]

from sklearn.model_selection import train_test_split
import lightgbm as lgb

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = lgb.LGBMRegressor(n_estimators=500, learning_rate=0.05, n_jobs=-1)
model.fit(X_train, y_train, eval_set=[(X_test, y_test)], callbacks=[lgb.early_stopping(30)])

joblib.dump(model, 'ttc_delay_model.joblib')
print("Model saved! Ready for the backend.")

