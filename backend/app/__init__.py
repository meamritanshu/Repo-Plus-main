"""
Flask application factory for RepoPulse.
"""

import logging
import os
from flask import Flask
from flask_cors import CORS


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder="static")
    CORS(app, origins="*")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Ensure static output directory exists
    graphs_dir = os.path.join(app.static_folder, "generated_graphs")
    os.makedirs(graphs_dir, exist_ok=True)

    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
