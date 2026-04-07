import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "attendance.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

BUZZER_ENABLED = True
BUZZER_PIN = 18

GSM_ENABLED = True
GSM_SERIAL_PORT = "/dev/serial0"
GSM_BAUDRATE = 9600
GSM_TIMEOUT = 2
DEFAULT_ALERT_NUMBER = "+917385520906"

SECRET_KEY = "change-this-in-production"
API_HOST = "0.0.0.0"
API_PORT = 5000

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

for _dir in (UPLOAD_DIR, LOG_DIR):
    os.makedirs(_dir, exist_ok=True)
