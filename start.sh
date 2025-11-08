#!/bin/bash

# UncarrierVibes Startup Script

echo "🚀 Starting UncarrierVibes..."
echo ""

# Set PostgreSQL path
export PATH="/Library/PostgreSQL/18/bin:$PATH"

# Activate virtual environment
source venv/bin/activate

# Start the API server in the background
echo "📡 Starting API server on http://localhost:8000"
uvicorn src.api.main:app --reload &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 10

# Start the dashboard in a new terminal
echo "📊 To start the dashboard, run in a new terminal:"
echo "   cd /Users/justin/UncarrierVibes"
echo "   source venv/bin/activate"
echo "   streamlit run src/dashboard/main.py"
echo ""
echo "✅ API server is running!"
echo ""
echo "🌐 Access points:"
echo "   • API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Dashboard: http://localhost:8501 (after starting streamlit)"
echo ""
echo "📝 To test the API, run: python test_api.py"
echo ""
echo "Press Ctrl+C to stop the API server"

# Wait for Ctrl+C
wait $API_PID