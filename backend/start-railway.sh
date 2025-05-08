#!/bin/bash
# Install uvicorn directly
pip install --break-system-packages uvicorn fastapi

# Run the application
python -m uvicorn api:app --host 0.0.0.0 --port $PORT
