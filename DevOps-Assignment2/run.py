"""
Entry point for the ACEest Fitness application.
Run from the DevOps-Assignment2/ directory:
    python run.py
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
