#!/bin/bash
# Print current directory for debugging
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la

# Install required packages directly
pip install --break-system-packages uvicorn==0.27.1 fastapi==0.110.0 python-dotenv==1.0.1 pydantic

# Run the application
python -m uvicorn api:app --host 0.0.0.0 --port $PORT
