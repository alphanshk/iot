"""Flask backend for IoT Smart Employee Attendance System."""

from __future__ import annotations

import base64
import csv
import io
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from buzzer import BuzzerService
from config import DB_PATH, DEBUG, FACE_REQUIRED, HOST, PORT, SAVED_FACES_DIR
from db_setup import init_db
from face import verify_employee_face
from gsm import GSMService

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

gsm_service = GSMService()
buzzer_service = BuzzerService()


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def current_date_time() -> tuple[str, str]:
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


def save_base64_image(employee_id: int, image_base64: str) -> str:
    """Decode base64 image and save as <employee_id>_<timestamp>.jpg."""
    SAVED_FACES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{employee_id}_{timestamp}.jpg"
    file_path = SAVED_FACES_DIR / filename

    if "," in image_base64:
        image_base64 = image_base64.split(",", maxsplit=1)[1]

    img_bytes = base64.b64decode(image_base64)
    file_path.write_bytes(img_bytes)
    return str(file_path)


@app.route("/")
def dashboard():
    """Render attendance dashboard."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT a.id, u.name, a.date, a.in_time, a.out_time
        FROM attendance a
        JOIN users u ON u.id = a.employee_id
        ORDER BY a.date DESC, COALESCE(a.out_time, a.in_time) DESC
        """
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", rows=rows)


@app.route("/login", methods=["POST"])
def login():
    """Authenticate user by phone and password."""
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", "")).strip()

    if not phone or not password:
        return jsonify({"success": False, "message": "Phone and password are required."}), 400

    conn = get_db_connection()
    user = conn.execute(
        "SELECT id, name, phone FROM users WHERE phone = ? AND password = ?",
        (phone, password),
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

    return jsonify(
        {
            "success": True,
            "message": "Login successful.",
            "employee": {"id": user["id"], "name": user["name"], "phone": user["phone"]},
        }
    )


@app.route("/mark_api", methods=["POST"])
def mark_attendance():
    """Mark attendance with IN/OUT logic and optional face verification."""
    try:
        data = request.get_json(silent=True) or {}
        employee_id = data.get("employee_id")
        image_base64 = data.get("image_base64")

        if not employee_id:
            buzzer_service.beep_error()
            return jsonify({"success": False, "message": "employee_id is required."}), 400

        try:
            employee_id = int(employee_id)
        except ValueError:
            buzzer_service.beep_error()
            return jsonify({"success": False, "message": "employee_id must be integer."}), 400

        if not image_base64:
            buzzer_service.beep_error()
            return jsonify({"success": False, "message": "image_base64 is required."}), 400

        saved_image_path = save_base64_image(employee_id, image_base64)

        # Optional face validation for low-memory compatibility.
        if FACE_REQUIRED:
            matched, face_message = verify_employee_face(employee_id, image_path=saved_image_path)
            if not matched:
                buzzer_service.beep_error()
                return jsonify({"success": False, "message": f"Face verification failed: {face_message}"}), 403

        today, now_time = current_date_time()
        conn = get_db_connection()

        user = conn.execute("SELECT id, name, phone FROM users WHERE id = ?", (employee_id,)).fetchone()
        if not user:
            conn.close()
            buzzer_service.beep_error()
            return jsonify({"success": False, "message": "Employee not found."}), 404

        attendance = conn.execute(
            "SELECT id, in_time, out_time FROM attendance WHERE employee_id = ? AND date = ?",
            (employee_id, today),
        ).fetchone()

        if attendance is None:
            conn.execute(
                "INSERT INTO attendance (employee_id, date, in_time, image_in_path) VALUES (?, ?, ?, ?)",
                (employee_id, today, now_time, saved_image_path),
            )
            mark_type = "IN"
        elif attendance["out_time"] is None:
            conn.execute(
                "UPDATE attendance SET out_time = ?, image_out_path = ? WHERE id = ?",
                (now_time, saved_image_path, attendance["id"]),
            )
            mark_type = "OUT"
        else:
            conn.close()
            buzzer_service.beep_error()
            return jsonify({"success": False, "message": "Already marked IN and OUT for today."}), 409

        conn.commit()
        conn.close()

        # Buzzer + GSM on success
        buzzer_service.beep_success()

        sms_msg = f"Employee {user['name']} marked {mark_type} at {now_time}"
        gsm_service.send_sms(user["phone"], sms_msg)

        return jsonify(
            {
                "success": True,
                "message": f"Attendance marked as {mark_type}.",
                "employee_id": employee_id,
                "date": today,
                "time": now_time,
                "type": mark_type,
                "image_path": saved_image_path,
            }
        )
    except Exception as exc:  # noqa: BLE001
        buzzer_service.beep_error()
        return jsonify({"success": False, "message": f"Server error: {exc}"}), 500


@app.route("/attendance", methods=["GET"])
def attendance_records():
    """Return attendance rows for all users or by filters."""
    employee_id = request.args.get("employee_id")
    date = request.args.get("date")

    q = (
        "SELECT a.id, u.name, u.phone, a.employee_id, a.date, a.in_time, a.out_time, "
        "a.image_in_path, a.image_out_path "
        "FROM attendance a JOIN users u ON u.id = a.employee_id WHERE 1=1"
    )
    params: list[str | int] = []

    if employee_id:
        q += " AND a.employee_id = ?"
        params.append(int(employee_id))
    if date:
        q += " AND a.date = ?"
        params.append(date)

    q += " ORDER BY a.date DESC, COALESCE(a.out_time, a.in_time) DESC"

    conn = get_db_connection()
    rows = conn.execute(q, params).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/export/excel", methods=["GET"])
def export_excel():
    """Download attendance in Excel format."""
    try:
        from openpyxl import Workbook
    except ImportError:
        return jsonify({"success": False, "message": "openpyxl not installed."}), 500

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT u.name, a.date, a.in_time, a.out_time
        FROM attendance a JOIN users u ON u.id = a.employee_id
        ORDER BY a.date DESC, COALESCE(a.out_time, a.in_time) DESC
        """
    ).fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"
    ws.append(["Name", "Date", "In Time", "Out Time"])
    for r in rows:
        ws.append([r["name"], r["date"], r["in_time"], r["out_time"]])

    mem = io.BytesIO()
    wb.save(mem)
    mem.seek(0)

    return send_file(
        mem,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="attendance.xlsx",
    )


@app.route("/export/csv", methods=["GET"])
def export_csv():
    """Download attendance in CSV format."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT u.name, a.date, a.in_time, a.out_time
        FROM attendance a JOIN users u ON u.id = a.employee_id
        ORDER BY a.date DESC, COALESCE(a.out_time, a.in_time) DESC
        """
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Date", "In Time", "Out Time"])
    for r in rows:
        writer.writerow([r["name"], r["date"], r["in_time"], r["out_time"]])

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="attendance.csv")


if __name__ == "__main__":
    init_db()
    app.run(host=HOST, port=PORT, debug=DEBUG)
