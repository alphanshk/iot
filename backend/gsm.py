import logging
import time

import serial

from config import (
    GSM_BAUDRATE,
    GSM_BOOT_WAIT_SECONDS,
    GSM_COMMAND_WAIT_SECONDS,
    GSM_ENABLED,
    GSM_SERIAL_PORT,
    GSM_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class Sim900AClient:
    def __init__(self) -> None:
        self.enabled = GSM_ENABLED

    def _send_cmd(self, ser: serial.Serial, cmd: str) -> str:
        ser.write((cmd + "\r").encode("utf-8"))
        time.sleep(GSM_COMMAND_WAIT_SECONDS)
        resp = ser.read_all().decode(errors="ignore")
        logger.debug("GSM CMD=%s RESP=%s", cmd, resp.strip())
        return resp

    def send_sms(self, phone: str, message: str) -> bool:
        if not self.enabled:
            logger.info("GSM disabled by config; skipping SMS")
            return False

        try:
            with serial.Serial(
                GSM_SERIAL_PORT,
                GSM_BAUDRATE,
                timeout=GSM_TIMEOUT_SECONDS,
            ) as ser:
                time.sleep(GSM_BOOT_WAIT_SECONDS)

                # Required exact sequence:
                # 1. AT
                # 2. AT+CMGF=1
                # 3. AT+CMGS="+91XXXXXXXXXX"
                # 4. <message>
                # 5. CTRL+Z
                self._send_cmd(ser, "AT")
                self._send_cmd(ser, "AT+CMGF=1")
                self._send_cmd(ser, f'AT+CMGS="{phone}"')

                ser.write(message.encode("utf-8"))
                time.sleep(0.2)
                ser.write(bytes([26]))  # CTRL+Z

                time.sleep(3)
                final_resp = ser.read_all().decode(errors="ignore")
                logger.info("SMS send response: %s", final_resp.strip())

                if "OK" in final_resp or "+CMGS:" in final_resp:
                    return True

                logger.warning("SIM900A did not confirm SMS delivery")
                return False
        except Exception as exc:
            logger.exception("SIM900A SMS send failed: %s", exc)
            return False
