import os
import sys

from flask import Flask
from flask_cors import CORS


# ============================================================
# AI FINANCE CONTROLLER
# API APPLICATION
# ============================================================


# ------------------------------------------------------------
# Project root
# ------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

if PROJECT_ROOT not in sys.path:

    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ============================================================
# Application Factory
# ============================================================

def create_app():

    app = Flask(__name__)

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    app.config["JSON_SORT_KEYS"] = False

    # --------------------------------------------------------
    # Enable CORS
    #
    # Allows the React frontend running on:
    # http://localhost:5173
    #
    # to communicate with this Flask API.
    # --------------------------------------------------------

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173"
                ]
            }
        }
    )

    # --------------------------------------------------------
    # Register routes
    # --------------------------------------------------------

    from src.api.routes import api

    app.register_blueprint(api)

    return app


# ============================================================
# Development Server
# ============================================================

if __name__ == "__main__":

    app = create_app()

    print("=" * 60)
    print("AI FINANCE CONTROLLER")
    print("BACKEND API")
    print("=" * 60)

    print(
        "\nStarting server..."
    )

    print(
        "URL: http://127.0.0.1:5000"
    )

    print(
        "Frontend: http://localhost:5173"
    )

    print(
        "CORS: ENABLED"
    )

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )