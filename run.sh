#!/bin/bash

# Configuration
PORT=8501
VENV_DIR=".venv"

# check if venv exists
if [ -d "$VENV_DIR" ]; then
    source $VENV_DIR/bin/activate
else
    echo "Warning: Virtual environment '$VENV_DIR' not found."
    echo "Please set it up first: python3 -m venv $VENV_DIR"
    exit 1
fi

# Run Streamlit
# --server.headless true disables the interactive browser opening on server
echo "Starting Streamlit App on port $PORT..."
streamlit run app.py --server.port $PORT --server.headless true
