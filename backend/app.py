import base64
import csv
import logging
import os
import sqlite3
from datetime import datetime
from io import BytesIO, StringIO
from uuid import uuid4

from flask import Flask, jsonify, request, send_file

from buzzer import AttendanceBuzzer
from config import DB_PATH, SAVED_FACES_DIR, UNLIMITED_MODE
from gsm import Sim900AClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("attendance_app")

app = Flask(__name__)
buzzer = AttendanceBuzzer()
gsm = Sim900AClient()


def get_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_base64_image(image_base64: str, employee_id: int) -> str:
    raw = base64.b64decode(image_base64)
    filename = f"emp_{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.jpg"
    path = os.path.join(SAVED_FACES_DIR, filename)
    with open(path, "wb") as f:
        f.write(raw)
    return path


def next_attendance_type(employee_id: int, date_str: str) -> str:
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM attendance
            WHERE employee_id = ? AND date = ?
            """,
            (employee_id, date_str),
        )
        count = cur.fetchone()["cnt"]

        if UNLIMITED_MODE:
            return "IN" if count % 2 == 0 else "OUT"

        # strict first IN, second OUT; further marks continue alternating safely
        if count == 0:
            return "IN"
        if count == 1:
            return "OUT"
        return "IN" if count % 2 == 0 else "OUT"
    finally:
        conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    phone = data.get("phone")
    password = data.get("password")

    if not phone or not password:
        return jsonify({"success": False, "message": "phone and password are required"}), 400

    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, phone FROM users WHERE phone = ? AND password = ?",
            (phone, password),
        )
        user = cur.fetchone()
        if not user:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

        return jsonify(
            {
                "success": True,
                "user": {
                    "id": user["id"],
                    "name": user["name"],
                    "phone": user["phone"],
                },
            }
        )
    finally:
        conn.close()


@app.route("/mark_api", methods=["POST"])
def mark_attendance():
    data = request.get_json(force=True)
    employee_id = data.get("employee_id")
    image_base64 = data.get("image_base64")

    if not employee_id or not image_base64:
        buzzer.error()
        return jsonify({"success": False, "message": "employee_id and image_base64 are required"}), 400

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, phone FROM users WHERE id = ?", (employee_id,))
        user = cur.fetchone()
        if not user:
            buzzer.error()
            return jsonify({"success": False, "message": "Employee not found"}), 404

        image_path = save_base64_image(image_base64, int(employee_id))
        mark_type = next_attendance_type(int(employee_id), date_str)

        cur.execute(
            """
            INSERT INTO attendance (employee_id, date, time, type, image_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_id, date_str, time_str, mark_type, image_path),
        )
        conn.commit()

        buzzer.success()

        sms_msg = f"Hi {user['name']}, Attendance {mark_type} marked at {time_str}"
        sms_ok = gsm.send_sms(user["phone"], sms_msg)
        if not sms_ok:
            logger.warning("Attendance saved but SMS failed for employee_id=%s", employee_id)

        return jsonify(
            {
                "success": True,
                "employee_id": employee_id,
                "name": user["name"],
                "type": mark_type,
                "date": date_str,
                "time": time_str,
                "image_path": image_path,
                "sms_sent": sms_ok,
            }
        )
    except Exception as exc:
        logger.exception("Failed to mark attendance: %s", exc)
        buzzer.error()
        return jsonify({"success": False, "message": "Internal server error"}), 500
    finally:
        conn.close()


@app.route("/attendance", methods=["GET"])
def attendance_list():
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.id, a.employee_id, u.name, a.date, a.time, a.type, a.image_path
            FROM attendance a
            JOIN users u ON u.id = a.employee_id
            ORDER BY a.date DESC, a.time DESC
            """
        )
        rows = [dict(r) for r in cur.fetchall()]
        return jsonify({"success": True, "records": rows})
    finally:
        conn.close()


@app.route("/export/csv", methods=["GET"])
def export_csv():
    conn = get_db_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.id, a.employee_id, u.name, a.date, a.time, a.type, a.image_path
            FROM attendance a
            JOIN users u ON u.id = a.employee_id
            ORDER BY a.id ASC
            """
        )
        rows = cur.fetchall()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "employee_id", "name", "date", "time", "type", "image_path"])
        for r in rows:
            writer.writerow([r["id"], r["employee_id"], r["name"], r["date"], r["time"], r["type"], r["image_path"]])

        csv_bytes = output.getvalue().encode("utf-8")
        return send_file(
            BytesIO(csv_bytes),
            mimetype="text/csv",
            as_attachment=True,
            download_name="attendance_export.csv",
        )
    finally:
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
