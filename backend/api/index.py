from os.path import dirname, abspath, join
import sys
import os

# Add the backend directory to the Python path
# This allows relative imports within the backend folder to work correctly
backend_dir = dirname(dirname(abspath(__file__)))
sys.path.append(backend_dir)

# Import the FastAPI app from main.py
from main import app

# This is required for Vercel to find the handler
# The filename must be index.py and the app must be named 'app'
handler = app
