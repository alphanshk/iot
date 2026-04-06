"""Flask backend for IoT Smart Employee Attendance System."""

from __future__ import annotations

import csv
import io
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from config import DB_PATH, DEBUG, FACE_REQUIRED, HOST, PORT
from db_setup import init_db
from face import save_uploaded_image, verify_employee_face
from gsm import GSMService

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

gsm_service = GSMService()


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def current_date_time() -> tuple[str, str]:
    now = datetime.now()
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


@app.route("/")
def dashboard():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT a.id, e.name, a.date, a.time, a.type
        FROM attendance a
        JOIN employees e ON e.id = a.employee_id
        ORDER BY a.date DESC, a.time DESC
        """
    ).fetchall()
    conn.close()
    return render_template("dashboard.html", rows=rows)


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", "")).strip()

    if not phone or not password:
        return jsonify({"success": False, "message": "Phone and password are required."}), 400

    conn = get_db_connection()
    row = conn.execute(
        "SELECT id, name, phone FROM employees WHERE phone = ? AND password = ?",
        (phone, password),
    ).fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

    return jsonify(
        {
            "success": True,
            "message": "Login successful.",
            "employee": {"id": row["id"], "name": row["name"], "phone": row["phone"]},
        }
    )


@app.route("/mark_api", methods=["POST"])
def mark_attendance():
    try:
        data = request.get_json(silent=True) or {}
        employee_id = data.get("employee_id") or request.form.get("employee_id")

        if not employee_id:
            return jsonify({"success": False, "message": "employee_id is required."}), 400

        try:
            employee_id = int(employee_id)
        except ValueError:
            return jsonify({"success": False, "message": "employee_id must be integer."}), 400

        # Optional face payload from JSON/base64 or multipart image upload.
        image_base64 = data.get("image_base64")
        image_path = None
        if "image" in request.files:
            img_file = request.files["image"]
            temp_path = Path("data") / "temp" / f"employee_{employee_id}_{datetime.now().timestamp()}.jpg"
            image_path = save_uploaded_image(img_file, temp_path)

        # Face validation (can be disabled for local/dev environments)
        if FACE_REQUIRED:
            matched, face_message = verify_employee_face(employee_id, image_base64=image_base64, image_path=image_path)
            if not matched:
                return jsonify({"success": False, "message": f"Face verification failed: {face_message}"}), 403

        today, now_time = current_date_time()
        conn = get_db_connection()

        emp = conn.execute("SELECT id, name, phone FROM employees WHERE id = ?", (employee_id,)).fetchone()
        if not emp:
            conn.close()
            return jsonify({"success": False, "message": "Employee not found."}), 404

        marks_today = conn.execute(
            "SELECT type, time FROM attendance WHERE employee_id = ? AND date = ? ORDER BY id ASC",
            (employee_id, today),
        ).fetchall()

        if len(marks_today) == 0:
            mark_type = "IN"
        elif len(marks_today) == 1:
            mark_type = "OUT"
        else:
            conn.close()
            return jsonify({"success": False, "message": "Already marked IN and OUT for today."}), 409

        conn.execute(
            "INSERT INTO attendance (employee_id, date, time, type) VALUES (?, ?, ?, ?)",
            (employee_id, today, now_time, mark_type),
        )
        conn.commit()
        conn.close()

        # GSM notifications
        base_msg = f"Attendance {mark_type} marked at {now_time} on {today}."
        gsm_service.send_sms(emp["phone"], f"Hi {emp['name']}, {base_msg}")

        if mark_type == "OUT":
            gsm_service.send_sms(emp["phone"], f"Hi {emp['name']}, final attendance confirmed for {today}.")

        return jsonify(
            {
                "success": True,
                "message": f"Attendance marked as {mark_type}.",
                "employee_id": employee_id,
                "date": today,
                "time": now_time,
                "type": mark_type,
            }
        )

    except Exception as exc:  # noqa: BLE001
        return jsonify({"success": False, "message": f"Server error: {exc}"}), 500


@app.route("/attendance", methods=["GET"])
def attendance_records():
    employee_id = request.args.get("employee_id")
    date = request.args.get("date")

    q = (
        "SELECT a.id, e.name, e.phone, a.employee_id, a.date, a.time, a.type "
        "FROM attendance a JOIN employees e ON e.id = a.employee_id WHERE 1=1"
    )
    params: list[str | int] = []

    if employee_id:
        q += " AND a.employee_id = ?"
        params.append(int(employee_id))
    if date:
        q += " AND a.date = ?"
        params.append(date)

    q += " ORDER BY a.date DESC, a.time DESC"

    conn = get_db_connection()
    rows = conn.execute(q, params).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])


@app.route("/export/csv", methods=["GET"])
def export_csv():
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT e.name, a.date, a.time, a.type
        FROM attendance a JOIN employees e ON e.id = a.employee_id
        ORDER BY a.date DESC, a.time DESC
        """
    ).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Date", "Time", "Type"])
    for r in rows:
        writer.writerow([r["name"], r["date"], r["time"], r["type"]])

    mem = io.BytesIO(output.getvalue().encode("utf-8"))
    return send_file(mem, mimetype="text/csv", as_attachment=True, download_name="attendance.csv")


@app.route("/export/excel", methods=["GET"])
def export_excel():
    try:
        from openpyxl import Workbook
    except ImportError:
        return jsonify({"success": False, "message": "openpyxl not installed. Add it to requirements."}), 500

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT e.name, a.date, a.time, a.type
        FROM attendance a JOIN employees e ON e.id = a.employee_id
        ORDER BY a.date DESC, a.time DESC
        """
    ).fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"
    ws.append(["Name", "Date", "Time", "Type"])
    for r in rows:
        ws.append([r["name"], r["date"], r["time"], r["type"]])

    mem = io.BytesIO()
    wb.save(mem)
    mem.seek(0)

    return send_file(
        mem,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="attendance.xlsx",
    )


if __name__ == "__main__":
    init_db()
    app.run(host=HOST, port=PORT, debug=DEBUG)
