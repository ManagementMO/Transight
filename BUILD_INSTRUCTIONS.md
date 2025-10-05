# Docker Build Instructions

## Backend (FastAPI ML Service)

### Build from root directory:
```bash
cd /root/Transight
docker build -f Dockerfile.backend -t transight-backend .
```

### Run:
```bash
docker run -p 8000:8000 transight-backend
```

### Test:
```bash
curl http://localhost:8000/health
```

## Frontend (React App)

### Build:
```bash
cd /root/Transight/frontend
docker build -t transight-frontend .
```

### Run:
```bash
docker run -p 80:80 transight-frontend
```

### Test:
```bash
curl http://localhost
```

## Deploy to Render

### Option 1: Using render.yaml (Recommended)
1. Push code to GitHub
2. Go to https://dashboard.render.com
3. New → Blueprint
4. Connect repo
5. Render auto-deploys both services

### Option 2: Manual Deployment

**Backend:**
1. New Web Service
2. Build Command: `cd machineLearning && pip install -r requirements.txt`
3. Start Command: `cd machineLearning && python app.py`
4. Add disk for model files

**Frontend:**
1. New Static Site
2. Build Command: `cd frontend && npm install && npm run build`
3. Publish Directory: `frontend/dist`
4. Environment: `VITE_API_BASE_URL=https://your-backend-url.onrender.com`

## Environment Variables

### Frontend
- `VITE_API_BASE_URL`: Backend API URL (set in .env.production)
- `VITE_MAPBOX_TOKEN`: Mapbox API token

### Backend
- `PORT`: Server port (default: 8000)
- `PYTHON_VERSION`: Python version (3.11.0)

## Important Files Needed for Deployment

### Backend:
- ✅ `machineLearning/ttc_delay_model.joblib` (5.5 MB)
- ✅ `dataAnalysis/geocoded_delays.parquet` (2.9 MB)
- ✅ `machineLearning/feature_importance.csv`

Make sure these files are committed to your repo or uploaded to Render's persistent disk!
