"""Database initialization script for Smart Attendance."""

import sqlite3
from pathlib import Path

from config import DATA_DIR, DB_PATH, KNOWN_FACES_DIR, SAVED_FACES_DIR


def init_db() -> None:
    """Initialize SQLite DB and required folders."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
    SAVED_FACES_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            in_time TEXT,
            out_time TEXT,
            image_in_path TEXT,
            image_out_path TEXT,
            FOREIGN KEY(employee_id) REFERENCES users(id),
            UNIQUE(employee_id, date)
        )
        """
    )

    # Seed demo users for multi-user system testing.
    demo_users = [
        ("Alphan", "9876543210", "admin123"),
        ("Priya", "9876543211", "pass123"),
    ]
    for name, phone, password in demo_users:
        cur.execute("SELECT id FROM users WHERE phone = ?", (phone,))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO users (name, phone, password) VALUES (?, ?, ?)",
                (name, phone, password),
            )
            print(f"Seeded user: {name} | {phone}")

    conn.commit()
    conn.close()
    print(f"Database initialized at: {Path(DB_PATH).resolve()}")


if __name__ == "__main__":
    init_db()
