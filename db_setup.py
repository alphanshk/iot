import logging
import sqlite3

from config import DB_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def setup_database() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
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
                time TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('IN', 'OUT')),
                image_path TEXT,
                FOREIGN KEY (employee_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()
        logging.info("Database setup complete at %s", DB_PATH)
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
