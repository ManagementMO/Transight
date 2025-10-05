# 🚍 Transight - TTC Delay Prediction System

An intelligent transit analytics platform that visualizes historical TTC bus delays and predicts future incidents using machine learning.

[![Live Demo](https://img.shields.io/badge/demo-live-success)](https://transight.onrender.com)
[![API](https://img.shields.io/badge/API-docs-blue)](https://transight-backend.onrender.com/docs)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

![Transight Dashboard](https://img.shields.io/badge/Built%20with-React%20%7C%20FastAPI%20%7C%20LightGBM-blueviolet)

---

## ✨ Features

### 📊 **Interactive Map Visualization**
- Real-time heatmap of TTC bus delays across Toronto (2014-2024)
- Time-lapse slider to traverse 10+ years of historical data
- Color-coded markers showing delay severity (green → yellow → red)

### 🔮 **AI-Powered Predictions**
- Machine learning model trained on 160,000+ delay incidents
- Predict delays for different incident scenarios (mechanical, collision, emergency, etc.)
- Route-specific forecasting with confidence intervals

### 📈 **Analytics Dashboard**
- Top delayed routes and stations
- Delay patterns by hour, day of week, and season
- Incident type breakdown and trends
- Real-time statistics

### 🔍 **Smart Search**
- Autocomplete station search
- Route comparison tool (compare up to 3 routes side-by-side)
- Location-based predictions

---

## 🛠️ Tech Stack

### **Frontend**
- **React** + **Vite** - Fast, modern UI framework
- **Tailwind CSS** - Utility-first styling
- **Mapbox GL JS** - Interactive map visualization
- **Recharts** - Data visualization library

### **Backend**
- **FastAPI** - High-performance Python API
- **LightGBM** - Gradient boosting ML model
- **Pandas** - Data processing
- **Scikit-learn** - Feature engineering & calibration

### **Data Pipeline**
- **160K geocoded delays** (2014-2024)
- **TTC GTFS data** for stop locations
- **100+ engineered features** (temporal, spatial, route-based)
- **Isotonic regression calibration** for accurate predictions

### **Deployment**
- **Docker** - Containerized deployment
- **Render.com** - Cloud hosting
- **Nginx** - Static file serving

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.11+
- Node.js 18+
- Mapbox API token (free tier works)

### **1. Backend Setup**
```bash
cd machineLearning
pip install -r requirements.txt
python app.py
```
Backend runs at: `http://localhost:8000`

### **2. Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:5173`

### **3. Environment Variables**

**Backend** - No configuration needed!

**Frontend** - Create `frontend/.env`:
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_MAPBOX_TOKEN=your_mapbox_token_here
```

---

## 📊 Machine Learning Model

### **Feature Engineering**
- **Temporal**: Hour, day of week, season, rush hour indicators
- **Spatial**: Distance from downtown, location frequency, spatial clustering
- **Route**: Route frequency, numeric route encoding
- **Cyclical encoding** for time-based features

### **Model Performance**
- **Algorithm**: LightGBM (gradient boosting)
- **Training**: 5-fold time-series cross-validation
- **Calibration**: Isotonic regression for prediction accuracy
- **Features**: 85+ engineered features
- **Data**: 160,079 historical incidents (2014-2024)

### **Recent Improvements** ✨
- ✅ Removed data leakage (incident/spatial averages)
- ✅ Added prediction calibration
- ✅ More accurate delay estimates

---

## 🎯 API Endpoints

### **Health Check**
```bash
GET /health
```

### **Historical Data** (Time-lapse visualization)
```bash
GET /api/historical?start=2024-01-01T00:00:00&end=2024-01-02T00:00:00
```

### **Predictions** (Scenario-based)
```bash
GET /api/predict?lat=43.7325&lon=-79.2631&route=36
```

### **Analytics**
```bash
GET /api/analytics/overview
```

### **Station Search**
```bash
GET /api/stations/search?query=kennedy
```

📖 **Full API documentation**: [https://transight-backend.onrender.com/docs](https://transight-backend.onrender.com/docs)

---

## 🐳 Docker Deployment

### **Backend**
```bash
docker build -f Dockerfile.backend -t transight-backend .
docker run -p 8000:8000 transight-backend
```

### **Frontend**
```bash
cd frontend
docker build \
  --build-arg VITE_API_BASE_URL=https://transight-backend.onrender.com \
  --build-arg VITE_MAPBOX_TOKEN=your_token \
  -t transight-frontend .
docker run -p 80:80 transight-frontend
```

---

## 📁 Project Structure

```
Transight/
├── machineLearning/          # Backend API & ML model
│   ├── app.py                # FastAPI server
│   ├── predictor.py          # ML prediction engine
│   ├── feature_engineering.py # Model training
│   ├── ttc_delay_model.joblib # Trained model (5.5 MB)
│   └── requirements.txt
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api/api.js        # API client
│   │   └── App.jsx           # Main app
│   ├── Dockerfile
│   └── nginx.conf
├── dataAnalysis/
│   └── geocoded_delays.parquet # Historical data (2.9 MB)
├── Dockerfile.backend        # Backend container
├── render.yaml               # Render deployment config
└── README.md
```

---

## 🎨 Design Philosophy

- **Minimalist UI** - Clean, Apple/Stripe-inspired design
- **Performance First** - Optimized API calls, lazy loading, caching
- **Accessibility** - Keyboard navigation, semantic HTML
- **Responsive** - Works on desktop, tablet, and mobile

---

## 🔬 Data Sources

- **TTC Delay Data**: 2014-2024 historical delays from TTC open data
- **GTFS Stops**: Station locations from TTC GTFS feed
- **Geocoding**: ~70% match rate using stop name matching
- **160,079 incidents** geocoded and processed

---

## 🚧 Future Enhancements

- [ ] Real-time delay alerts via WebSocket
- [ ] User accounts & saved routes
- [ ] Mobile app (React Native)
- [ ] Integration with TTC NextBus API
- [ ] Predictive routing suggestions
- [ ] Multi-city support

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

Built with ❤️ by a transit enthusiast who's tired of being late

---

## 🙏 Acknowledgments

- **TTC** for providing open data
- **Mapbox** for beautiful maps
- **Render.com** for free hosting
- **Claude** for code assistance and debugging

---

## 📞 Support

- 🌐 **Live Demo**: [https://transight.onrender.com](https://transight.onrender.com)
- 📚 **API Docs**: [https://transight-backend.onrender.com/docs](https://transight-backend.onrender.com/docs)
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/transight/issues)

---

<p align="center">
  <strong>Made for Torontonians, by Torontonians 🍁</strong>
</p>
