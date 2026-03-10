#!/bin/bash
# ZenBot Startup Script - Simple HTML Frontend

echo "🚀 Starting ZenBot..."
echo ""
echo "Starting FastAPI server with static HTML frontend..."
echo ""
echo "────────────────────────────────────────────────────────────"
echo "📱 Open: http://localhost:8000"
echo "📊 API: http://localhost:8000/health"
echo "────────────────────────────────────────────────────────────"
echo ""

cd backend
python3 app.py
