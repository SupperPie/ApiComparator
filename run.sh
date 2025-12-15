#!/bin/bash

# Configuration
PORT=8501
# Run Streamlit
# --server.headless true disables the interactive browser opening on server
echo "Starting Streamlit App on port $PORT..."
streamlit run app.py --server.port $PORT --server.headless true
