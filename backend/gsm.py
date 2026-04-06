"""GSM utility for SIM800L SMS sending using AT commands."""

from __future__ import annotations

import time

from config import GSM_BAUDRATE, GSM_ENABLED, GSM_SERIAL_PORT, GSM_TIMEOUT_SECONDS


class GSMService:
    """Service wrapper to send SMS via SIM800L module."""

    def __init__(self) -> None:
        self.enabled = GSM_ENABLED
        self.serial_port = GSM_SERIAL_PORT
        self.baudrate = GSM_BAUDRATE
        self.timeout = GSM_TIMEOUT_SECONDS

    def send_sms(self, phone: str, message: str) -> bool:
        """Send SMS message; returns True on success.

        If GSM is disabled, message is logged and returns True for local testing.
        """
        if not self.enabled:
            print(f"[GSM-DRYRUN] SMS to {phone}: {message}")
            return True

        try:
            import serial

            with serial.Serial(self.serial_port, self.baudrate, timeout=self.timeout) as ser:
                self._write_cmd(ser, "AT")
                self._write_cmd(ser, "AT+CMGF=1")
                self._write_cmd(ser, f'AT+CMGS="{phone}"')
                ser.write(message.encode("utf-8"))
                ser.write(b"\x1A")  # CTRL+Z
                time.sleep(3)
                response = ser.read_all().decode(errors="ignore")
                ok = "OK" in response or "+CMGS" in response
                print(f"[GSM] Response: {response}")
                return ok
        except Exception as exc:  # noqa: BLE001
            print(f"[GSM] SMS failed: {exc}")
            return False

    @staticmethod
    def _write_cmd(ser, cmd: str) -> None:
        ser.write((cmd + "\r").encode("utf-8"))
        time.sleep(1)
        _ = ser.read_all()
