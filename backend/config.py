"""Configuration for Smart Attendance backend.

Environment variables are supported for easier deployment on Raspberry Pi, Linux,
and Windows development machines.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "attendance.db"
KNOWN_FACES_DIR = DATA_DIR / "known_faces"

# Flask
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# GSM (SIM800L)
DEFAULT_GSM_PORT = "COM3" if platform.system().lower().startswith("win") else "/dev/serial0"
GSM_ENABLED = os.getenv("GSM_ENABLED", "false").lower() == "true"
GSM_SERIAL_PORT = os.getenv("GSM_SERIAL_PORT", DEFAULT_GSM_PORT)
GSM_BAUDRATE = int(os.getenv("GSM_BAUDRATE", "9600"))
GSM_TIMEOUT_SECONDS = int(os.getenv("GSM_TIMEOUT_SECONDS", "2"))

# Face recognition
FACE_MATCH_TOLERANCE = float(os.getenv("FACE_MATCH_TOLERANCE", "0.5"))
FACE_REQUIRED = os.getenv("FACE_REQUIRED", "true").lower() == "true"
