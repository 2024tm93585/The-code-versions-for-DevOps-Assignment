import sqlite3
import os


PROGRAMS = {
    "Fat Loss (FL) - 3 day": {"factor": 22, "desc": "3-day full-body fat loss"},
    "Fat Loss (FL) - 5 day": {"factor": 24, "desc": "5-day split, higher volume fat loss"},
    "Muscle Gain (MG) - PPL": {"factor": 35, "desc": "Push/Pull/Legs hypertrophy"},
    "Beginner (BG)": {"factor": 26, "desc": "3-day simple beginner full-body"},
}


def get_db_path(app):
    """Return the database path from app config."""
    db = app.config.get('DATABASE', 'aceest_fitness.db')
    if db == ':memory:':
        return db
    if not os.path.isabs(db):
        db = os.path.join(app.instance_path, db)
    return db


def get_db(app):
    """Return a new SQLite connection."""
    db_path = get_db_path(app)
    if db_path == ':memory:':
        # For in-memory testing, store connection on app to reuse
        if not hasattr(app, '_test_db_conn'):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            app._test_db_conn = conn
        return app._test_db_conn
    # Ensure the directory exists before connecting
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(app):
    """Create all tables if they do not exist."""
    conn = get_db(app)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            age INTEGER NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
            program TEXT NOT NULL,
            calories INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            date TEXT NOT NULL,
            weight REAL,
            notes TEXT,
            FOREIGN KEY (client_name) REFERENCES clients(name)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            workout_date TEXT NOT NULL,
            workout_type TEXT NOT NULL,
            duration_minutes INTEGER,
            notes TEXT,
            FOREIGN KEY (client_name) REFERENCES clients(name)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_id INTEGER NOT NULL,
            exercise_name TEXT NOT NULL,
            sets INTEGER,
            reps INTEGER,
            weight_kg REAL,
            FOREIGN KEY (workout_id) REFERENCES workouts(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            metric_date TEXT NOT NULL,
            bmi REAL,
            body_fat_pct REAL,
            muscle_mass_kg REAL,
            FOREIGN KEY (client_name) REFERENCES clients(name)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'staff',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()


def calculate_calories(weight, program):
    """Calculate daily calorie target based on weight (kg) and program name."""
    program_data = PROGRAMS.get(program)
    if not program_data:
        return 0
    return int(weight * program_data["factor"])


def get_all_clients(app):
    """Return a list of all clients as dicts."""
    conn = get_db(app)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, age, height, weight, program, calories, created_at FROM clients ORDER BY name'
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_client_by_name(app, name):
    """Return a single client dict by name, or None if not found."""
    conn = get_db(app)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, name, age, height, weight, program, calories, created_at FROM clients WHERE name = ?',
        (name,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def save_client(app, name, age, height, weight, program):
    """Insert or replace a client record. Returns True on success, False on failure."""
    try:
        calories = calculate_calories(weight, program)
        conn = get_db(app)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT OR REPLACE INTO clients (name, age, height, weight, program, calories)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (name, int(age), float(height), float(weight), program, calories)
        )
        conn.commit()
        return True
    except Exception:
        return False


def delete_client(app, name):
    """Delete a client by name. Returns True if a row was deleted, False otherwise."""
    try:
        conn = get_db(app)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM clients WHERE name = ?', (name,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception:
        return False


def get_programs():
    """Return the programs dictionary."""
    return PROGRAMS
