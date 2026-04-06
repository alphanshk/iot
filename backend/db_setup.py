"""Database initialization script for Smart Attendance."""

import sqlite3
from pathlib import Path

from config import DATA_DIR, DB_PATH


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
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
            time TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('IN', 'OUT')),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
        """
    )

    # Seed demo employee if not present
    cur.execute("SELECT id FROM employees WHERE phone = ?", ("9876543210",))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO employees (name, phone, password) VALUES (?, ?, ?)",
            ("Admin User", "9876543210", "admin123"),
        )
        print("Seeded demo employee: phone=9876543210 password=admin123")

    conn.commit()
    conn.close()
    print(f"Database initialized at: {Path(DB_PATH).resolve()}")


if __name__ == "__main__":
    init_db()
