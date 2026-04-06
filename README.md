# IoT Smart Employee Attendance System (Android + Flask + Raspberry Pi)

A complete attendance system with:
- Android Kotlin app (login, fingerprint, camera capture)
- Flask backend on Raspberry Pi
- SQLite database
- Optional face verification
- Buzzer GPIO feedback
- Optional GSM SMS alerts
- Web dashboard with Excel export

---

## 1) Project Structure

```text
iot/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── db_setup.py
│   ├── buzzer.py
│   ├── gsm.py
│   ├── face.py
│   ├── requirements.txt
│   ├── requirements-1gb.txt
│   ├── requirements-windows.txt
│   ├── data/
│   │   ├── attendance.db            # generated
│   │   ├── known_faces/             # reference faces: <employee_id>.jpg
│   │   └── saved_faces/             # captured attendance images
│   ├── templates/
│   │   └── dashboard.html
│   └── static/css/
│       └── styles.css
└── android-app/
    └── app/src/main/java/com/example/attendance/
        ├── LoginActivity.kt
        ├── DashboardActivity.kt
        ├── ApiService.kt
        ├── SessionManager.kt
        └── Models.kt
```

---

## 2) Core Features Implemented

- Multi-user login (`phone + password`)
- Fingerprint auth in Android via `BiometricPrompt`
- Camera capture + Base64 upload from Android
- Attendance logic:
  - first mark/day = IN
  - second mark/day = OUT
  - third attempt/day = rejected
- Captured image save in `backend/data/saved_faces/` as `<employee_id>_<timestamp>.jpg`
- Buzzer support:
  - `beep_success()` => short beep
  - `beep_error()` => 3 beeps
- Optional GSM SMS for IN/OUT
- Web dashboard + CSV/Excel export
- Face recognition optional (`FACE_REQUIRED=false` by default for 1GB devices)

---

## 3) Backend API

### POST `/login`
```json
{ "phone": "9876543210", "password": "admin123" }
```

### POST `/mark_api`
```json
{ "employee_id": 1, "image_base64": "<base64_jpg>" }
```

### GET `/attendance`
Optional query: `employee_id`, `date`

---

## 4) Database Schema

- `users(id, name, phone, password)`
- `attendance(id, employee_id, date, in_time, out_time, image_in_path, image_out_path)`

---

## 5) Raspberry Pi Setup (Full)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python db_setup.py
python app.py
```

Server runs on `0.0.0.0:5000`.

---

## 6) Raspberry Pi Setup (1GB Optimized)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-1gb.txt
export FACE_REQUIRED=false
python db_setup.py
python app.py
```

This mode is recommended on Raspberry Pi 5 (1GB RAM).

---

## 7) Windows Setup

If NumPy/face packages fail on Windows, use:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements-windows.txt
$env:FACE_REQUIRED = "false"
python db_setup.py
python app.py
```

---

## 8) GPIO Buzzer Wiring

- Buzzer signal -> GPIO18
- GND -> GND

Config:
- `BUZZER_ENABLED=true`
- `BUZZER_PIN=18`

Behavior:
- Success mark => one short beep
- Failure/rejection => three short beeps

---

## 9) GSM SIM800L (Optional)

Set env:
- `GSM_ENABLED=true`
- `GSM_SERIAL_PORT=/dev/serial0` (Pi) or `COM3` (Windows)

SMS sent on:
- IN marked
- OUT marked

---

## 10) Android Integration

In `android-app/.../ApiService.kt`, set:

```kotlin
private const val BASE_URL = "http://<RASPBERRY_PI_IP>:5000/"
```

App flow:
1. Login with phone/password
2. Fingerprint verification
3. Camera capture
4. Base64 image sent to `/mark_api`
5. Show IN/OUT/failure response

---

## 11) Face Recognition Mode

- Default: `FACE_REQUIRED=false` (optimized)
- For strict mode:
  - set `FACE_REQUIRED=true`
  - store reference face at `backend/data/known_faces/<employee_id>.jpg`

---

## 12) Demo Users

After `python db_setup.py`:
- `9876543210 / admin123`
- `9876543211 / pass123`

