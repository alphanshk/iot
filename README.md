# IoT Smart Employee Attendance System

A complete IoT attendance solution using:
- **Flask** backend (Python)
- **SQLite** database
- **Raspberry Pi 5 peripherals**
  - Buzzer on GPIO18 via `gpiozero`/`lgpio`
  - SIM900A GSM via `pyserial`
- **Android app** (Kotlin) for login + fingerprint + camera capture

## Project Structure

- `config.py` – runtime configuration and auto-created directories
- `db_setup.py` – SQLite schema creation
- `buzzer.py` – GPIO18 buzzer integration
- `gsm.py` – SIM900A AT-command SMS integration
- `app.py` – Flask APIs, dashboard, exports
- `templates/admin.html` – admin panel
- `android_app/` – Android Kotlin app source
- `requirements.txt` – Python dependencies

## Backend Setup

1. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize database:
   ```bash
   python db_setup.py
   ```

4. Run server:
   ```bash
   python app.py
   ```

Server runs at:
- `http://0.0.0.0:5000`
- Health check: `GET /health`

## API Endpoints

### Auth
- `POST /register`
  - JSON: `{ "name": "User", "phone": "9999999999", "password": "pass" }`
- `POST /login`
  - JSON: `{ "phone": "9999999999", "password": "pass" }`

### Attendance
- `POST /mark_api`
  - JSON:
    ```json
    {
      "employee_id": 1,
      "phone": "9999999999",
      "image_base64": "<base64-image>"
    }
    ```
  - Automatically marks `IN` / `OUT` alternately per user per day.

### Admin and Exports
- `GET /admin?username=admin&password=admin123`
- `GET /export/csv`
- `GET /export/excel`
- `GET /export/user/<id>`

## Raspberry Pi 5 Hardware Notes

### Buzzer
- Uses `gpiozero.Buzzer`
- Pin: **GPIO18** (BCM mode)

### GSM SIM900A
- Serial port default: `/dev/serial0`
- Baudrate: `9600`
- AT flow:
  - `AT`
  - `AT+CMGF=1`
  - `AT+CMGS="<number>"`
  - `<message>` + `CTRL+Z`

If GSM or buzzer hardware is unavailable, API remains stable and returns valid JSON responses.

## Android App

Located in `android_app/`.

Main flow:
1. Login with phone/password
2. Capture image from camera
3. Fingerprint authentication (BiometricPrompt)
4. Convert image to Base64
5. Call `POST /mark_api`
6. Show API response

> Update backend URL in:
> `android_app/app/src/main/java/com/iot/attendance/ApiService.kt`
> with your Raspberry Pi IP.

## Default Config

From `config.py`:
- `BUZZER_ENABLED = True`
- `BUZZER_PIN = 18`
- `GSM_ENABLED = True`
- `GSM_SERIAL_PORT = "/dev/serial0"`
- `GSM_BAUDRATE = 9600`
- Default SMS number: `+917385520906`

## Dependency List

Python packages:
- flask
- pyserial
- gpiozero
- lgpio
- pillow
- openpyxl

## Quick Verification

```bash
python db_setup.py
python -m py_compile app.py buzzer.py gsm.py db_setup.py config.py
python app.py
```

