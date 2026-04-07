import logging
import time

from gpiozero import Buzzer

from config import BUZZER_ENABLED, BUZZER_PIN

logger = logging.getLogger(__name__)


class AttendanceBuzzer:
    def __init__(self) -> None:
        self._buzzer = None
        if not BUZZER_ENABLED:
            logger.info("Buzzer disabled by config")
            return

        try:
            # gpiozero automatically uses lgpio on Raspberry Pi 5 when lgpio is installed.
            self._buzzer = Buzzer(BUZZER_PIN)
            logger.info("Buzzer initialized on GPIO%s", BUZZER_PIN)
        except Exception as exc:
            logger.exception("Failed to initialize buzzer: %s", exc)

    def _beep(self, count: int, on_seconds: float = 0.12, off_seconds: float = 0.12) -> None:
        if not self._buzzer:
            return

        for _ in range(count):
            self._buzzer.on()
            time.sleep(on_seconds)
            self._buzzer.off()
            time.sleep(off_seconds)

    def success(self) -> None:
        self._beep(count=1)

    def error(self) -> None:
        self._beep(count=3)
