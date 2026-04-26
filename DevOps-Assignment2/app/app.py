"""
Flask application module.
Import create_app from here or use run.py at the project root.
"""
import sys
import os

# Allow running this file directly: python app/app.py
# by adding the project root to sys.path so 'from app import create_app' works.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
