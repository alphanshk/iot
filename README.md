# IoT Smart Employee Attendance System

Complete Raspberry Pi + Flask + SQLite + Android project for secure employee attendance using:

- Phone/password login
- Mobile fingerprint verification (BiometricPrompt)
- Face recognition check before attendance marking
- GSM SMS notifications for IN/OUT/final status
- Web dashboard with CSV/Excel exports

## Folder Structure

```text
iot/
├── README.md
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── db_setup.py
│   ├── face.py
│   ├── gsm.py
│   ├── requirements.txt
│   ├── data/
│   │   ├── attendance.db           # generated
│   │   └── known_faces/            # store employee face images as <employee_id>.jpg
│   ├── static/
│   │   └── css/
│   │       └── styles.css
│   └── templates/
│       └── dashboard.html
└── android-app/
    ├── settings.gradle
    ├── build.gradle
    ├── gradle.properties
    └── app/
        ├── build.gradle
        └── src/main/
            ├── AndroidManifest.xml
            ├── java/com/example/attendance/
            │   ├── ApiService.kt
            │   ├── DashboardActivity.kt
            │   ├── LoginActivity.kt
            │   ├── Models.kt
            │   └── SessionManager.kt
            └── res/
                ├── layout/
                │   ├── activity_dashboard.xml
                │   └── activity_login.xml
                └── values/
                    ├── colors.xml
                    ├── strings.xml
                    └── themes.xml
```

## 1) Backend Setup (Raspberry Pi)

### Install system dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libatlas-base-dev cmake build-essential libopenblas-dev liblapack-dev
```

For webcam and face recognition support:

```bash
sudo apt install -y libjpeg-dev libtiff5-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
```

### Python setup

```bash
cd /workspace/iot/backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Initialize database and demo employee

```bash
python db_setup.py
```

Demo credentials:
- Phone: `9876543210`
- Password: `admin123`

### Add known face images

Place employee reference photos in:

```text
backend/data/known_faces/<employee_id>.jpg
```

Example for employee ID 1:

```bash
cp myphoto.jpg backend/data/known_faces/1.jpg
```

### Run Flask server on Raspberry Pi LAN

```bash
python app.py
```

Server listens on:
- `http://0.0.0.0:5000`
- Access in LAN as `http://<RPI_LOCAL_IP>:5000`

## 2) GSM (SIM800L) Wiring and Usage

- Connect SIM800L TX -> Raspberry Pi RX (GPIO15, pin 10)
- Connect SIM800L RX -> Raspberry Pi TX (GPIO14, pin 8)
- Common GND required
- Use stable external 4V power for SIM800L (do **not** power directly from Pi 3.3V pin)

Edit values in `backend/config.py`:
- `GSM_SERIAL_PORT` (e.g. `/dev/serial0`)
- `GSM_BAUDRATE`
- `GSM_ENABLED = True` once hardware is ready

When enabled, system sends SMS for:
1. IN marked
2. OUT marked
3. Final confirmation after OUT

## 3) API Endpoints

### POST `/login`
Body:
```json
{
  "phone": "9876543210",
  "password": "admin123"
}
```

### POST `/mark_api`
Body (JSON or multipart):
```json
{
  "employee_id": 1,
  "image_base64": "<optional base64 jpeg>"
}
```

Attendance logic:
- First mark of day -> `IN`
- Second mark of day -> `OUT`
- Third+ attempt -> reject as already marked

### GET `/attendance`
Optional query params:
- `employee_id`
- `date` (YYYY-MM-DD)

### GET `/` (Web dashboard)
Shows live attendance table and export buttons.

## 4) Android App Setup

1. Open `android-app/` in Android Studio.
2. Let Gradle sync.
3. In `ApiService.kt`, update `BASE_URL` to Raspberry Pi LAN IP, e.g.:
   - `http://192.168.1.23:5000/`
4. Run on Android 9+ device with fingerprint enrolled.

### App Flow
- Login screen: phone + password
- Dashboard: Mark Attendance button
- On mark:
  1. BiometricPrompt fingerprint validation
  2. Capture image (camera intent)
  3. POST `/mark_api` with employee ID and image
  4. Show IN/OUT/rejection message

## 5) Preventing Proxy Attendance

Implemented controls:
- Password-based account authentication
- On-device biometric fingerprint check before mark request
- Server-side face verification against stored employee face
- Daily IN/OUT sequence restriction (max 2 valid marks)

## 6) Production Notes

- Replace plain password storage with hashed passwords (bcrypt/argon2) before production.
- Add JWT/session token validation for every API.
- Add HTTPS (Nginx reverse proxy + TLS).
- Use proper SMS queue/retry logic for unstable networks.
- Configure camera quality and liveness checks for stronger anti-spoofing.

