import base64
import csv
import logging
import os
import sqlite3
from datetime import datetime
from io import BytesIO

from flask import Flask, jsonify, render_template, request, send_file
from openpyxl import Workbook
from PIL import Image

from buzzer import AttendanceBuzzer
from config import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    API_HOST,
    API_PORT,
    DB_PATH,
    LOG_FILE,
    SECRET_KEY,
    UPLOAD_DIR,
)
from db_setup import setup_database
from gsm import GSMService

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

buzzer = AttendanceBuzzer()
gsm = GSMService()


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def save_base64_image(image_b64: str, employee_id: int) -> str | None:
    if not image_b64:
        return None

    try:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]

        image_data = base64.b64decode(image_b64)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        date_folder = datetime.now().strftime("%Y-%m-%d")
        target_dir = os.path.join(UPLOAD_DIR, date_folder)
        os.makedirs(target_dir, exist_ok=True)

        filename = f"emp_{employee_id}_{datetime.now().strftime('%H%M%S_%f')}.jpg"
        file_path = os.path.join(target_dir, filename)
        image.save(file_path, "JPEG", quality=85)
        return file_path
    except Exception:
        logger.exception("Failed to decode or save image")
        return None


def determine_attendance_type(conn: sqlite3.Connection, employee_id: int, date_str: str) -> str:
    cur = conn.cursor()
    cur.execute(
        "SELECT type FROM attendance WHERE employee_id = ? AND date = ? ORDER BY id DESC LIMIT 1",
        (employee_id, date_str),
    )
    row = cur.fetchone()
    if not row:
        return "IN"
    return "OUT" if row["type"] == "IN" else "IN"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.utcnow().isoformat()})


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    password = (data.get("password") or "").strip()

    if not all([name, phone, password]):
        return jsonify({"success": False, "message": "name, phone, password required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(name, phone, password) VALUES (?, ?, ?)",
            (name, phone, password),
        )
        conn.commit()
        return jsonify({"success": True, "user_id": cur.lastrowid, "message": "User registered"})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Phone already registered"}), 409
    except Exception:
        logger.exception("Registration failed")
        return jsonify({"success": False, "message": "Server error"}), 500
    finally:
        if "conn" in locals():
            conn.close()


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    password = (data.get("password") or "").strip()

    if not phone or not password:
        return jsonify({"success": False, "message": "phone and password required"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, phone FROM users WHERE phone = ? AND password = ?", (phone, password))
        user = cur.fetchone()
        if not user:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        return jsonify(
            {
                "success": True,
                "message": "Login successful",
                "user": {"id": user["id"], "name": user["name"], "phone": user["phone"]},
            }
        )
    except Exception:
        logger.exception("Login failed")
        return jsonify({"success": False, "message": "Server error"}), 500
    finally:
        if "conn" in locals():
            conn.close()


@app.route("/mark_api", methods=["POST"])
def mark_attendance():
    data = request.get_json(silent=True) or {}

    employee_id = data.get("employee_id")
    image_b64 = data.get("image_base64")
    user_phone = data.get("phone")

    if not employee_id:
        buzzer.beep_error()
        return jsonify({"success": False, "message": "employee_id required"}), 400

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id, name, phone FROM users WHERE id = ?", (employee_id,))
        user = cur.fetchone()
        if not user:
            buzzer.beep_error()
            return jsonify({"success": False, "message": "User not found"}), 404

        attendance_type = determine_attendance_type(conn, employee_id, date_str)
        image_path = save_base64_image(image_b64, employee_id)

        cur.execute(
            """
            INSERT INTO attendance(employee_id, date, time, type, image_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (employee_id, date_str, time_str, attendance_type, image_path),
        )
        conn.commit()

        buzzer_result = buzzer.beep_success()

        sms_text = (
            f"Attendance {attendance_type} marked for {user['name']} "
            f"on {date_str} at {time_str}."
        )
        sms_result = gsm.send_sms(sms_text, number=(user_phone or user["phone"]))

        return jsonify(
            {
                "success": True,
                "message": f"Attendance marked as {attendance_type}",
                "data": {
                    "employee_id": employee_id,
                    "name": user["name"],
                    "date": date_str,
                    "time": time_str,
                    "type": attendance_type,
                    "image_path": image_path,
                    "buzzer": buzzer_result,
                    "sms": sms_result,
                },
            }
        )
    except Exception:
        logger.exception("mark_api failed")
        buzzer.beep_error()
        return jsonify({"success": False, "message": "Server error while marking attendance"}), 500
    finally:
        if "conn" in locals():
            conn.close()


@app.route("/admin", methods=["GET"])
def admin_dashboard():
    username = request.args.get("username", "")
    password = request.args.get("password", "")
    if username != ADMIN_USERNAME or password != ADMIN_PASSWORD:
        return jsonify(
            {
                "success": False,
                "message": "Pass ?username=admin&password=admin123 query params for dashboard access",
            }
        ), 401

    conn = get_db_connection()
    try:
        users = conn.execute("SELECT id, name, phone FROM users ORDER BY id DESC").fetchall()
        attendance = conn.execute(
            """
            SELECT a.id, a.employee_id, u.name, u.phone, a.date, a.time, a.type, a.image_path
            FROM attendance a
            JOIN users u ON u.id = a.employee_id
            ORDER BY a.id DESC
            """
        ).fetchall()
        return render_template("admin.html", users=users, attendance=attendance)
    finally:
        conn.close()


def _fetch_attendance(conn: sqlite3.Connection, user_id: int | None = None):
    base_query = (
        "SELECT a.id, u.name, u.phone, a.date, a.time, a.type, a.image_path "
        "FROM attendance a JOIN users u ON u.id = a.employee_id"
    )
    params: tuple = ()
    if user_id is not None:
        base_query += " WHERE a.employee_id = ?"
        params = (user_id,)
    base_query += " ORDER BY a.id DESC"
    return conn.execute(base_query, params).fetchall()


@app.route("/export/csv", methods=["GET"])
def export_csv():
    conn = get_db_connection()
    try:
        rows = _fetch_attendance(conn)
        output = BytesIO()
        text_buffer = output

        import io

        string_io = io.StringIO()
        writer = csv.writer(string_io)
        writer.writerow(["ID", "Name", "Phone", "Date", "Time", "Type", "Image Path"])
        for row in rows:
            writer.writerow([row["id"], row["name"], row["phone"], row["date"], row["time"], row["type"], row["image_path"]])

        text_buffer.write(string_io.getvalue().encode("utf-8"))
        text_buffer.seek(0)
        return send_file(text_buffer, mimetype="text/csv", as_attachment=True, download_name="attendance_report.csv")
    finally:
        conn.close()


@app.route("/export/excel", methods=["GET"])
def export_excel():
    conn = get_db_connection()
    try:
        rows = _fetch_attendance(conn)
        wb = Workbook()
        ws = wb.active
        ws.title = "Attendance"
        ws.append(["ID", "Name", "Phone", "Date", "Time", "Type", "Image Path"])
        for row in rows:
            ws.append([row["id"], row["name"], row["phone"], row["date"], row["time"], row["type"], row["image_path"]])

        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name="attendance_report.xlsx",
        )
    finally:
        conn.close()


@app.route("/export/user/<int:user_id>", methods=["GET"])
def export_user(user_id: int):
    conn = get_db_connection()
    try:
        rows = _fetch_attendance(conn, user_id=user_id)
        if not rows:
            return jsonify({"success": False, "message": "No attendance for user"}), 404

        output = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = f"User_{user_id}"
        ws.append(["ID", "Name", "Phone", "Date", "Time", "Type", "Image Path"])
        for row in rows:
            ws.append([row["id"], row["name"], row["phone"], row["date"], row["time"], row["type"], row["image_path"]])
        wb.save(output)
        output.seek(0)
        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=f"attendance_user_{user_id}.xlsx",
        )
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
    app.run(host=API_HOST, port=API_PORT, debug=False)
