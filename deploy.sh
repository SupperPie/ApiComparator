#!/bin/bash

# Deployment Script for ApiComparator
# Usage: ./deploy.sh

echo "🚀 Starting Deployment..."

# 1. Pull latest changes
echo "⬇️ Pulling latest code..."
git pull origin $(git rev-parse --abbrev-ref HEAD)

# 2. Install Dependencies
echo "📦 Installing/Updating Dependencies..."
pip install -r requirements.txt

# 3. Check for existing process and kill it
PID=$(ps -ef | grep "streamlit run app.py" | grep -v grep | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "🛑 Stopping existing application (PID: $PID)..."
    kill -9 $PID
else
    echo "ℹ️ No running application found."
fi

# 4. Start Application in Background
echo "▶️ Starting Application..."
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > app.log 2>&1 &

NEW_PID=$!
echo "✅ Application started successfully! (PID: $NEW_PID)"
echo "📄 Logs are being written to app.log"
echo "🌍 Access via http://<server-ip>:8501"
