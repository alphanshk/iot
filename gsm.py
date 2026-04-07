import logging
import time

import serial

from config import DEFAULT_ALERT_NUMBER, GSM_BAUDRATE, GSM_ENABLED, GSM_SERIAL_PORT, GSM_TIMEOUT

logger = logging.getLogger(__name__)


class GSMService:
    def __init__(self) -> None:
        self.enabled = GSM_ENABLED

    def _send_command(self, ser: serial.Serial, cmd: str, wait: float = 0.8) -> str:
        ser.write((cmd + "\r").encode())
        time.sleep(wait)
        output = ser.read_all().decode(errors="ignore")
        logger.debug("AT command '%s' response: %s", cmd, output.strip())
        return output

    def send_sms(self, message: str, number: str | None = None) -> dict:
        target_number = number or DEFAULT_ALERT_NUMBER
        if not self.enabled:
            return {"success": False, "reason": "GSM disabled", "number": target_number}

        try:
            with serial.Serial(GSM_SERIAL_PORT, GSM_BAUDRATE, timeout=GSM_TIMEOUT) as ser:
                self._send_command(ser, "AT")
                self._send_command(ser, "AT+CMGF=1")
                ser.write(f'AT+CMGS="{target_number}"\r'.encode())
                time.sleep(1)
                ser.write(message.encode())
                ser.write(bytes([26]))  # CTRL+Z
                time.sleep(3)
                response = ser.read_all().decode(errors="ignore")

                ok = "OK" in response or "+CMGS" in response
                if not ok:
                    logger.error("SMS send failed response: %s", response.strip())
                return {
                    "success": ok,
                    "number": target_number,
                    "response": response.strip(),
                }
        except Exception as exc:
            logger.exception("GSM SMS sending failed")
            return {"success": False, "number": target_number, "reason": str(exc)}
