#!/bin/bash

# Install Python and pip
apt-get update
apt-get install -y python3 python3-pip

# Install dependencies
pip3 install -r requirements.txt

# Start the application
python3 -m uvicorn api:app --host 0.0.0.0 --port $PORT
