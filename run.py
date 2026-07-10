"""Local development entry point.

Run with: python run.py
This is also the command Docker uses to start the container (see Dockerfile).
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
