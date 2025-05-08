#!/bin/bash
# Print current directory for debugging
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la

# Find Python paths
echo "Python paths:"
which python
which python3

# Install required packages directly
pip install --break-system-packages uvicorn==0.27.1 fastapi==0.110.0 python-dotenv==1.0.1 pydantic

# Run the application with the correct Python path
/usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT
