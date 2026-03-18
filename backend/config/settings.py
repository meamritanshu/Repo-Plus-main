"""
Configuration settings for RepoPulse backend.
"""

import os

# Base directory of the backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directory where temporary repos are cloned
TEMP_REPO_DIR = os.path.join(BASE_DIR, "data", "temp_repos")

# Directory where generated graphs are saved
GRAPH_OUTPUT_DIR = os.path.join(BASE_DIR, "app", "static", "generated_graphs")

# Maximum number of commits to analyze (performance guard)
MAX_COMMITS = 500

# Risk score weights
RISK_WEIGHTS = {
    "frequency": 0.6,
    "churn": 0.4,
}

# Top N files to display
TOP_N_FILES = 15

# Logging level
LOG_LEVEL = "INFO"

# Flask settings
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
HOST = "0.0.0.0"
PORT = 5000
