# TTC Delay Prediction System - Quick Start

## Prerequisites
- Python 3.8+
- Node.js 16+
- Mapbox API token (already configured in frontend/.env)

## Backend Setup & Launch

```bash
cd /root/Transight/machineLearning

# Install dependencies
pip install fastapi uvicorn pandas scikit-learn lightgbm python-dateutil

# Start the API server (port 8000)
python api.py
```

**Backend will be available at:** `http://localhost:8000`
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Frontend Setup & Launch

```bash
cd /root/Transight/frontend

# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

**Frontend will be available at:** `http://localhost:5173`

## Application Features

### 1. Historical Data Visualization
- Time-series slider to traverse 2014-2024 delay data
- Heatmap overlay showing delay severity
- Color-coded markers (green=low, yellow=medium, red=high)

### 2. Interactive Map
- Click any delay point to view details
- Popup shows: Route, Delay, Incident, Location
- Sidebar opens with predictions

### 3. Route-Specific Predictions
- 3-hour delay forecast chart
- Scenario-based predictions for different incident types
- Location details and statistics

### 4. Design
- Minimalist Stripe/Apple-inspired UI
- Inter font with soft shadows
- Smooth animations and transitions
- Responsive layout

## API Endpoints

- `GET /api/time-range` - Available data range
- `GET /api/historical` - Time-lapse data
- `GET /api/predict` - Scenario predictions
- `GET /api/incident-types` - Available incident types

## Data Pipeline

1. **Preprocessing:** `backend/preprocess_ttc_data.py`
   - Processes 2014-2024 Excel files
   - Outputs: `geocoded_delays.parquet`

2. **Feature Engineering:** `machineLearning/feature_engineering.py`
   - 100+ engineered features
   - LightGBM model training
   - Outputs: `delay_model.pkl`

3. **Geocoding:** `dataAnalysis/geocode.py`
   - stops.txt-based location matching
   - 69.9% match rate

## Tech Stack

**Backend:**
- FastAPI
- LightGBM
- Pandas/NumPy

**Frontend:**
- React + Vite
- Tailwind CSS
- Mapbox GL JS
- Recharts

**Data:**
- 160K geocoded delays (2014-2024)
- TTC stops.txt
- Trained ML model
