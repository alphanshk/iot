import logging
from time import sleep

from config import BUZZER_ENABLED, BUZZER_PIN

logger = logging.getLogger(__name__)

try:
    from gpiozero import Buzzer
except Exception as exc:  # pragma: no cover (hardware specific)
    Buzzer = None
    logger.warning("gpiozero import failed: %s", exc)


class AttendanceBuzzer:
    def __init__(self) -> None:
        self.enabled = BUZZER_ENABLED and Buzzer is not None
        self.device = None
        if self.enabled:
            try:
                self.device = Buzzer(BUZZER_PIN)
                logger.info("Buzzer initialized on pin %s", BUZZER_PIN)
            except Exception as exc:
                logger.error("Buzzer initialization failed: %s", exc)
                self.enabled = False

    def beep_success(self) -> bool:
        if not self.enabled or self.device is None:
            return False
        try:
            self.device.on()
            sleep(0.15)
            self.device.off()
            return True
        except Exception as exc:
            logger.error("Buzzer success beep failed: %s", exc)
            return False

    def beep_error(self) -> bool:
        if not self.enabled or self.device is None:
            return False
        try:
            for _ in range(2):
                self.device.on()
                sleep(0.1)
                self.device.off()
                sleep(0.1)
            return True
        except Exception as exc:
            logger.error("Buzzer error beep failed: %s", exc)
            return False
