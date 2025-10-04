# In your main.py for FastAPI
import pandas as pd
from fastapi import FastAPI
app = FastAPI()

# Load the data ONCE when the server starts
df_full = pd.read_parquet('ttc_bus_delays_master_with_geo.parquet') # Use Parquet!
df_full['month'] = pd.to_datetime(df_full['datetime']).dt.month

@app.get("/api/yearly-summary")
async def get_yearly_summary():
    # Group data by route and month, calculate average delay
    # and keep one representative coordinate for the route.
    summary = df_full.groupby(['route', 'month']).agg(
        avg_delay=('min_delay', 'mean'),
        incident_count=('min_delay', 'size'),
        latitude=('latitude', 'first'),
        longitude=('longitude', 'first')
    ).reset_index()
    
    # Convert this DataFrame to JSON that the frontend can use
    return summary.to_dict(orient='records')