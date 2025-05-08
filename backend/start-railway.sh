#!/bin/bash
echo "Current directory: $(pwd)"
echo "Listing files:"
ls -la
echo "Full file tree:"
find . -type f -name "*.py" | sort

echo "Python paths:"
which python
which python3

# Install required packages directly
pip install --break-system-packages uvicorn==0.27.1 fastapi==0.110.0 python-dotenv==1.0.0 pydantic requests

# Try to run from the directory where api.py is found
if [ -f "./api.py" ]; then
  echo "Found api.py in current directory"
  /usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT
elif [ -f "./backend/api.py" ]; then
  echo "Found api.py in ./backend"
  cd backend
  /usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT
elif [ -f "./suna/backend/api.py" ]; then
  echo "Found api.py in ./suna/backend"
  cd suna/backend
  /usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT
else
  echo "Could not find api.py! Searching for it..."
  API_PATH=$(find / -name "api.py" -type f 2>/dev/null | head -1)
  if [ -n "$API_PATH" ]; then
    echo "Found api.py at $API_PATH"
    cd $(dirname "$API_PATH")
    echo "Changed directory to $(pwd)"
    /usr/bin/python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT
  else
    echo "Could not find api.py anywhere!"
    exit 1
  fi
fi
