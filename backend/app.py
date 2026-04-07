import base64
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request

try:
    import RPi.GPIO as GPIO
except Exception:  # pragma: no cover - development fallback
    GPIO = None

try:
    import serial
except Exception:  # pragma: no cover - development fallback
    serial = None

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAVE_DIR = DATA_DIR / "saved_faces"
DB_PATH = DATA_DIR / "attendance.db"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

BUZZER_PIN = 18
SERIAL_PORT = "/dev/ttyS0"
SERIAL_BAUD = 9600

app = Flask(__name__)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL CHECK (type IN ('IN', 'OUT')),
            FOREIGN KEY(employee_id) REFERENCES users(id)
        );
        """
    )

    default_phone = "7385520906"
    existing = conn.execute("SELECT id FROM users WHERE phone = ?", (default_phone,)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users(name, phone, password) VALUES (?, ?, ?)",
            ("Alphan", default_phone, "admin123"),
        )
    conn.commit()
    conn.close()


class Buzzer:
    def __init__(self, pin: int):
        self.pin = pin
        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.OUT)

    def _pulse(self, duration: float = 0.15):
        if GPIO:
            GPIO.output(self.pin, GPIO.HIGH)
            time.sleep(duration)
            GPIO.output(self.pin, GPIO.LOW)
        else:
            print(f"[BUZZER] Pulse {duration}s")

    def success(self):
        self._pulse(0.12)

    def error(self):
        for _ in range(3):
            self._pulse(0.1)
            time.sleep(0.08)


class SmsSender:
    def __init__(self, port: str, baud_rate: int):
        self.port = port
        self.baud_rate = baud_rate

    def send_sms(self, phone: str, message: str):
        if not serial:
            print(f"[GSM] SMS to {phone}: {message}")
            return

        modem = serial.Serial(self.port, self.baud_rate, timeout=1)
        try:
            modem.write(b"AT\r")
            time.sleep(0.5)
            modem.write(b"AT+CMGF=1\r")
            time.sleep(0.5)
            modem.write(f'AT+CMGS="{phone}"\r'.encode())
            time.sleep(0.5)
            modem.write(message.encode() + b"\x1A")
            time.sleep(2)
        finally:
            modem.close()


buzzer = Buzzer(BUZZER_PIN)
sms_sender = SmsSender(SERIAL_PORT, SERIAL_BAUD)


def parse_payload(required_fields):
    data = request.get_json(silent=True) or {}
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return None, (jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400)
    return data, None


@app.post("/register")
def register():
    data, error = parse_payload(["name", "phone", "password"])
    if error:
        buzzer.error()
        return error

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users(name, phone, password) VALUES (?, ?, ?)",
            (data["name"], data["phone"], data["password"]),
        )
        conn.commit()
        user_id = conn.execute("SELECT id FROM users WHERE phone = ?", (data["phone"],)).fetchone()["id"]
        conn.close()
        buzzer.success()
        return jsonify({"message": "Registration successful", "user_id": user_id}), 201
    except sqlite3.IntegrityError:
        buzzer.error()
        return jsonify({"error": "Phone already exists"}), 409


@app.post("/login")
def login():
    data, error = parse_payload(["phone", "password"])
    if error:
        buzzer.error()
        return error

    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, name, phone FROM users WHERE phone = ? AND password = ?",
        (data["phone"], data["password"]),
    ).fetchone()
    conn.close()

    if row:
        return jsonify({"message": "Login success", "user": dict(row)})

    buzzer.error()
    return jsonify({"error": "Invalid credentials"}), 401


@app.post("/mark_api")
def mark_attendance():
    data, error = parse_payload(["employee_id", "image_base64"])
    if error:
        buzzer.error()
        return error

    employee_id = int(data["employee_id"])
    conn = get_db_connection()
    user = conn.execute("SELECT id, name, phone FROM users WHERE id = ?", (employee_id,)).fetchone()
    if not user:
        conn.close()
        buzzer.error()
        return jsonify({"error": "Invalid employee_id"}), 404

    last_record = conn.execute(
        "SELECT type FROM attendance WHERE employee_id = ? ORDER BY id DESC LIMIT 1",
        (employee_id,),
    ).fetchone()
    mark_type = "IN" if not last_record or last_record["type"] == "OUT" else "OUT"

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    timestamp = now.strftime("%Y%m%d_%H%M%S")
    image_file = SAVE_DIR / f"{employee_id}_{timestamp}.jpg"
    try:
        with image_file.open("wb") as img_out:
            img_out.write(base64.b64decode(data["image_base64"]))
    except Exception:
        conn.close()
        buzzer.error()
        return jsonify({"error": "Invalid image_base64"}), 400

    conn.execute(
        "INSERT INTO attendance(employee_id, date, time, type) VALUES (?, ?, ?, ?)",
        (employee_id, date_str, time_str, mark_type),
    )
    conn.commit()
    conn.close()

    sms_text = f"Hi {user['name']}, Attendance {mark_type} marked at {now.strftime('%I:%M %p')}"
    sms_sender.send_sms(user["phone"], sms_text)
    buzzer.success()

    return jsonify(
        {
            "message": "Attendance marked",
            "employee_id": employee_id,
            "type": mark_type,
            "date": date_str,
            "time": time_str,
            "image": str(image_file.relative_to(BASE_DIR)),
        }
    )


@app.get("/attendance")
def attendance_list():
    employee_id = request.args.get("employee_id")

    conn = get_db_connection()
    if employee_id:
        rows = conn.execute(
            """
            SELECT a.id, a.employee_id, u.name, u.phone, a.date, a.time, a.type
            FROM attendance a
            JOIN users u ON a.employee_id = u.id
            WHERE a.employee_id = ?
            ORDER BY a.id DESC
            """,
            (employee_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT a.id, a.employee_id, u.name, u.phone, a.date, a.time, a.type
            FROM attendance a
            JOIN users u ON a.employee_id = u.id
            ORDER BY a.id DESC
            """
        ).fetchall()

    conn.close()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
