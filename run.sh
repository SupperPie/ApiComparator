#!/bin/bash

# Configuration
PORT=8501
# Run Streamlit
# --server.headless true disables the interactive browser opening on server
echo "Starting Streamlit App on port $PORT..."
python3 -m streamlit run app.py --server.port $PORT --server.headless true
