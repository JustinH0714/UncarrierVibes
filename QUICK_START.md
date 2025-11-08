# 🚀 Quick Start Guide

## Your UncarrierVibes Application is Ready!

Everything has been set up for your T-Mobile hackathon project. Here's how to get started:

## ✅ What's Installed

- ✅ Python virtual environment with all dependencies
- ✅ PostgreSQL database (uncarrier_vibes)
- ✅ Sentiment analysis ML model (DistilBERT)
- ✅ FastAPI backend with routes
- ✅ Streamlit dashboard
- ✅ Test scripts and documentation

## 🎯 How to Run

### Option 1: One-Command Start (Easiest)
```bash
cd /Users/justin/UncarrierVibes
./start.sh
```

### Option 2: Manual Start

**Terminal 1 - API Server**:
```bash
cd /Users/justin/UncarrierVibes
export PATH="/Library/PostgreSQL/18/bin:$PATH"
source venv/bin/activate
uvicorn src.api.main:app --reload
```

**Terminal 2 - Dashboard** (optional):
```bash
cd /Users/justin/UncarrierVibes
source venv/bin/activate
streamlit run src/dashboard/main.py
```

## 🧪 Test It

Once the server is running, test it:

```bash
# In a new terminal
cd /Users/justin/UncarrierVibes
source venv/bin/activate
python test_api.py
```

Or manually:
```bash
curl -X POST "http://localhost:8000/api/v1/feedback/submit?text=T-Mobile%20is%20awesome!"
```

## 🌐 Access Points

After starting the application:

- **API Server**: http://localhost:8000
- **API Docs** (Swagger UI): http://localhost:8000/docs
- **Dashboard** (if running): http://localhost:8501

## 📊 What You Can Do

### 1. Submit Feedback
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/feedback/submit",
    params={"text": "The 5G coverage is amazing!"}
)
print(response.json())
```

### 2. Get Statistics
```bash
curl http://localhost:8000/api/v1/feedback/stats
```

### 3. View Sentiment Trends
```bash
curl http://localhost:8000/api/v1/metrics/sentiment-trend?days=7
```

### 4. Use WebSockets
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    console.log('Received:', event.data);
};
```

## 🎨 Demo Script

Here's a quick demo you can run:

```bash
# 1. Start the server
./start.sh

# 2. In another terminal, run the test script
python test_api.py

# 3. Open the API docs
open http://localhost:8000/docs

# 4. Try submitting feedback via the docs interface
```

## 📁 Project Structure

```
UncarrierVibes/
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # Main app
│   │   ├── routes/       # API endpoints
│   │   └── websocket.py  # WebSocket handler
│   ├── ml/               # Sentiment analysis
│   │   └── sentiment.py  # ML model
│   ├── db/               # Database
│   │   └── database.py   # DB models
│   └── dashboard/        # Streamlit dashboard
│       └── main.py       # Dashboard app
├── test_api.py           # Test script
├── start.sh              # Startup script
├── requirements.txt      # Dependencies
├── .env                  # Configuration
└── README.md             # Documentation
```

## 🔧 Troubleshooting

### Server won't start
```bash
# Check if PostgreSQL is running
export PATH="/Library/PostgreSQL/18/bin:$PATH"
psql -U postgres -l

# Check if port 8000 is in use
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000

# Restart the server
uvicorn src.api.main:app --reload
```

### Database connection error
- Make sure your password in `.env` is correct
- Check PostgreSQL is running
- Database name is `uncarrier_vibes`

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## 🚀 For Your Presentation

Key points to highlight:

1. **Real-time Analysis**: Sentiment is analyzed instantly as feedback comes in
2. **ML-Powered**: Uses state-of-the-art transformer models
3. **Production-Ready**: Complete with API docs, error handling, and tests
4. **Scalable**: Modular architecture can handle growth
5. **Interactive**: Dashboard provides visual insights

## 📊 Sample Data for Demo

Use these examples in your presentation:

**Positive Feedback**:
- "T-Mobile's 5G network is incredibly fast!"
- "Best customer service I've ever experienced"
- "Love the unlimited data plan"

**Negative Feedback**:
- "Service keeps dropping in my area"
- "Billing issues every month"
- "Customer support wait times are too long"

**Mixed**:
- "Great speeds but expensive plans"
- "Good coverage in cities, poor in rural areas"

## 🎯 Next Steps

1. **Customize**: Add your own features and endpoints
2. **Enhance**: Improve the dashboard with more visualizations
3. **Scale**: Add caching, authentication, rate limiting
4. **Deploy**: Consider deploying to Heroku, AWS, or Google Cloud

## 💡 Tips for the Hackathon

- Start the server before your presentation
- Have test data ready
- Show the API docs (they're interactive!)
- Demonstrate real-time sentiment analysis
- Explain the business value (early issue detection, customer insights)

## 📞 Need Help?

- Check `README.md` for detailed documentation
- See `PROJECT_SUMMARY.md` for architecture overview
- Review API docs at http://localhost:8000/docs
- Run `python test_api.py` to verify everything works

## ✨ You're All Set!

Your UncarrierVibes application is fully functional and ready for the hackathon. Good luck! 🍀