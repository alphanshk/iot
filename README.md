# IoT Smart Employee Attendance System

## Stack
- Android app (Kotlin)
- Flask backend on Raspberry Pi 5
- SQLite database
- GPIO buzzer on GPIO18 (gpiozero + lgpio backend)
- GSM SIM900A SMS integration through `/dev/serial0`

## Backend files
- `backend/app.py`: Flask APIs (`/login`, `/mark_api`, `/attendance`, `/export/csv`)
- `backend/gsm.py`: Real SIM900A AT command SMS send
- `backend/buzzer.py`: Success/error buzzer patterns
- `backend/db_setup.py`: DB schema initialization
- `backend/config.py`: Hardware and runtime config

## Raspberry Pi 5 prerequisites
1. Enable UART:
   ```bash
   sudo raspi-config
   # Interface Options -> Serial
   # Disable login shell, Enable serial hardware
   ```
2. Ensure gpiozero works with lgpio backend:
   ```bash
   sudo apt update
   sudo apt install -y python3-lgpio
   ```
3. Wire SIM900A:
   - TX -> GPIO15 (RX)
   - RX -> GPIO14 (TX)
   - GND -> GND
   - External supply **12V/2A mandatory** (do not power from Pi 5)

## Install and run backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python db_setup.py
python app.py
```

## Android app
Set API URL in `android-app/app/src/main/java/com/example/iotattendance/api/ApiClient.kt`:
```kotlin
private const val BASE_URL = "http://<RASPBERRY_PI_IP>:5000/"
```

Then open `android-app` in Android Studio and run on device.

## API examples
### Login
`POST /login`
```json
{
  "phone": "+919999999999",
  "password": "1234"
}
```

### Mark attendance
`POST /mark_api`
```json
{
  "employee_id": 1,
  "image_base64": "..."
}
```
