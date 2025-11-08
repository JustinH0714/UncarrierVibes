# UncarrierVibes - T-Mobile Customer Sentiment Analysis

Real-time sentiment analysis platform for capturing and analyzing T-Mobile customer feedback.

## Features

- Real-time sentiment analysis of customer feedback
- Live data streaming and processing
- Interactive dashboards for visualization
- API endpoints for data access
- Automatic issue detection and alerting
- Historical trend analysis

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **ML/AI**: Transformers (Hugging Face)
- **Frontend**: Streamlit
- **Real-time Updates**: WebSockets
- **Data Processing**: Pandas, NumPy

## Project Structure

```
UncarrierVibes/
├── src/
│   ├── api/            # FastAPI application
│   │   ├── routes/     # API route handlers
│   │   ├── main.py     # Main FastAPI app
│   │   └── websocket.py # WebSocket manager
│   ├── db/             # Database models and connections
│   ├── ml/             # Sentiment analysis models
│   └── dashboard/      # Streamlit dashboard
├── tests/              # Unit and integration tests
├── test_api.py         # API test script
├── start.sh            # Startup script
└── requirements.txt    # Python dependencies
```

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 18
- Virtual environment

### Installation

1. **Activate virtual environment** (already created):
```bash
source venv/bin/activate
```

2. **Set PostgreSQL PATH**:
```bash
export PATH="/Library/PostgreSQL/18/bin:$PATH"
```

3. **Update the `.env` file** with your PostgreSQL password:
```bash
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/uncarrier_vibes
MODEL_NAME=distilbert-base-uncased-finetuned-sst-2-english
```

### Running the Application

#### Option 1: Using the startup script
```bash
./start.sh
```

#### Option 2: Manual startup

**Terminal 1 - Start the API server**:
```bash
export PATH="/Library/PostgreSQL/18/bin:$PATH"
source venv/bin/activate
uvicorn src.api.main:app --reload
```

**Terminal 2 - Start the Dashboard**:
```bash
source venv/bin/activate
streamlit run src/dashboard/main.py
```

### Testing the API

Run the test script:
```bash
python test_api.py
```

Or test manually:
```bash
# Submit feedback
curl -X POST "http://localhost:8000/api/v1/feedback/submit?text=T-Mobile%20has%20great%20service!"

# Get stats
curl "http://localhost:8000/api/v1/feedback/stats"

# Get metrics
curl "http://localhost:8000/api/v1/metrics/summary"
```

## API Endpoints

### Feedback
- `POST /api/v1/feedback/submit` - Submit new feedback
- `GET /api/v1/feedback/latest` - Get latest feedback
- `GET /api/v1/feedback/stats` - Get feedback statistics

### Sentiment Analysis
- `POST /api/v1/sentiment/analyze` - Analyze sentiment of text
- `POST /api/v1/sentiment/batch-analyze` - Batch analyze multiple texts

### Metrics
- `GET /api/v1/metrics/summary` - Get metrics summary
- `GET /api/v1/metrics/sentiment-trend` - Get sentiment trends

### WebSocket
- `WS /ws` - Real-time updates

## Access Points

- **API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501

## Development

The sentiment analysis uses DistilBERT model fine-tuned for sentiment analysis. The model is automatically downloaded on first run.

To add new features:
1. Create new routes in `src/api/routes/`
2. Add ML models in `src/ml/`
3. Update dashboard visualizations in `src/dashboard/`

## Troubleshooting

**Database connection error**:
- Ensure PostgreSQL is running
- Check your password in `.env` file
- Verify database exists: `psql -U postgres -l`

**Import errors**:
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

**Model download issues**:
- Ensure you have internet connection
- The model (~268MB) will be downloaded on first run

## License

This project was created for the T-Mobile hackathon.