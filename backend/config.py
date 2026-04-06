"""Configuration for Smart Attendance backend."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "attendance.db"
KNOWN_FACES_DIR = DATA_DIR / "known_faces"

# Flask
SECRET_KEY = "change-me-in-production"
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True

# GSM (SIM800L)
GSM_ENABLED = False
GSM_SERIAL_PORT = "/dev/serial0"
GSM_BAUDRATE = 9600
GSM_TIMEOUT_SECONDS = 2

# Face recognition
FACE_MATCH_TOLERANCE = 0.5
