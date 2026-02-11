#!/usr/bin/env python3
"""AYA - Teams Meeting Summarizer
Run this file to start the web application.
"""

from app.config import Config
from app.web import create_app

app = create_app()

if __name__ == "__main__":
    print(f"\n  AYA Teams Meeting Summarizer")
    print(f"  Running on http://localhost:{Config.PORT}")
    print(f"  Press Ctrl+C to quit\n")
    app.run(host="0.0.0.0", port=Config.PORT, debug=True)
