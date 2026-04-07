import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SAVED_FACES_DIR = os.path.join(DATA_DIR, "saved_faces")
DB_PATH = os.path.join(DATA_DIR, "attendance.db")

BUZZER_ENABLED = True
BUZZER_PIN = 18

GSM_ENABLED = True
GSM_SERIAL_PORT = "/dev/serial0"
GSM_BAUDRATE = 9600
GSM_TIMEOUT_SECONDS = 2

# Optional: Set True to allow unlimited IN/OUT toggles instead of strict first IN, second OUT
UNLIMITED_MODE = False

# SIM900A timing controls
GSM_BOOT_WAIT_SECONDS = 0.5
GSM_COMMAND_WAIT_SECONDS = 0.3

os.makedirs(SAVED_FACES_DIR, exist_ok=True)
