# ✅ Deployment Ready - TTC Delay Prediction System

## Backend Configuration
- **URL**: `https://transight-backend.onrender.com`
- **Framework**: FastAPI + LightGBM ML model
- **Port**: 8000
- **Health Check**: `/health`

### Files:
✅ `Dockerfile.backend` (at root)
✅ `.dockerignore` (at root)
✅ `machineLearning/requirements.txt`
✅ `machineLearning/app.py`
✅ `machineLearning/predictor.py`
✅ `machineLearning/ttc_delay_model.joblib` (5.5 MB)
✅ `dataAnalysis/geocoded_delays.parquet` (2.9 MB)

## Frontend Configuration
- **Framework**: React + Vite + Tailwind CSS
- **API URL**: Configured via `VITE_API_BASE_URL`
- **Build Output**: `dist/`

### Files:
✅ `frontend/Dockerfile`
✅ `frontend/.dockerignore`
✅ `frontend/nginx.conf`
✅ `frontend/.env.production` (backend URL configured)
✅ `frontend/src/api/api.js` (centralized API calls)

## API Integration - All Components Updated
✅ **SearchBar.jsx** - Uses environment variable
✅ **RouteComparison.jsx** - Uses environment variable
✅ **Analytics.jsx** - Uses environment variable
✅ **MapView.jsx** - Uses centralized API functions

## Environment Variables

### Production (.env.production)
```bash
VITE_API_BASE_URL=https://transight-backend.onrender.com
VITE_MAPBOX_TOKEN=pk.eyJ1IjoibWFwYm94bW8xMjMiLCJhIjoiY21jcXN5dXdqMDFrODJqcTBhcnppb3QzMSJ9.do-_5cjmbfnW2o-FyMofvA
```

### Local Development (.env)
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_MAPBOX_TOKEN=pk.eyJ1IjoibWFwYm94bW8xMjMiLCJhIjoiY21jcXN5dXdqMDFrODJqcTBhcnppb3QzMSJ9.do-_5cjmbfnW2o-FyMofvA
```

## Deployment Options

### 🎯 Option 1: Render.com (Recommended)
```bash
# 1. Push to GitHub
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. Deploy on Render
# - Go to https://dashboard.render.com
# - New → Blueprint
# - Connect your repo
# - render.yaml will auto-configure both services
```

### 🐳 Option 2: Docker Build & Deploy

**Backend:**
```bash
cd /root/Transight
docker build -f Dockerfile.backend -t transight-backend .
docker run -p 8000:8000 transight-backend
```

**Frontend:**
```bash
cd /root/Transight/frontend
docker build \
  --build-arg VITE_API_BASE_URL=https://transight-backend.onrender.com \
  -t transight-frontend .
docker run -p 80:80 transight-frontend
```

### 🛠️ Option 3: Manual Build

**Backend:**
```bash
cd machineLearning
pip install -r requirements.txt
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run build  # Uses .env.production
npm run preview  # Test production build locally
```

## What's Fixed

### ✅ Docker Build Context Issue
- Moved `Dockerfile.backend` to root directory
- Changed COPY paths to work from root context
- Updated `.dockerignore` to include necessary files

### ✅ API URL Configuration
- All hardcoded `localhost:8000` URLs removed
- Centralized API configuration in `api/api.js`
- Environment-based URL switching (dev/prod)

### ✅ ML Model Improvements (Bonus!)
- Removed data leakage from training
- Added prediction calibration
- More accurate delay predictions

## Testing Checklist

### Backend:
- [ ] `curl https://transight-backend.onrender.com/health`
- [ ] Check `/docs` for API documentation
- [ ] Test `/api/time-range` endpoint

### Frontend:
- [ ] Build completes successfully
- [ ] API calls connect to backend
- [ ] Map loads with Mapbox token
- [ ] Search functionality works
- [ ] Analytics dashboard loads

## Important Notes

1. **Model & Data Files**: Make sure these are in your Git repo or uploaded to Render:
   - `machineLearning/ttc_delay_model.joblib`
   - `dataAnalysis/geocoded_delays.parquet`

2. **CORS**: Backend already configured with `allow_origins=["*"]` for development. For production, update to specific domain.

3. **Backend URL**: If you change the backend URL, update:
   - `frontend/.env.production`
   - `render.yaml` (frontend env vars)

Ready to deploy! 🚀
