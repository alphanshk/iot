"""GPIO buzzer feedback helper for Raspberry Pi.

- beep_success(): short single beep
- beep_error(): three short beeps
"""

from __future__ import annotations

import time

from config import BUZZER_ENABLED, BUZZER_PIN


class BuzzerService:
    """Wrapper around RPi.GPIO with safe no-op fallback on non-Pi systems."""

    def __init__(self) -> None:
        self.enabled = BUZZER_ENABLED
        self.pin = BUZZER_PIN
        self._gpio = None

        if not self.enabled:
            return

        try:
            import RPi.GPIO as GPIO

            self._gpio = GPIO
            self._gpio.setmode(GPIO.BCM)
            self._gpio.setup(self.pin, GPIO.OUT)
            self._gpio.output(self.pin, GPIO.LOW)
        except Exception as exc:  # noqa: BLE001
            print(f"[BUZZER] GPIO unavailable, fallback to logs only: {exc}")
            self._gpio = None

    def beep_success(self) -> None:
        """Single short beep for success."""
        self._beep(0.15, repeats=1)

    def beep_error(self) -> None:
        """Three short beeps for failures."""
        self._beep(0.12, repeats=3, gap=0.12)

    def _beep(self, duration: float, repeats: int = 1, gap: float = 0.1) -> None:
        if not self.enabled:
            print(f"[BUZZER-DRYRUN] beep repeats={repeats} duration={duration}")
            return

        for _ in range(repeats):
            if self._gpio:
                self._gpio.output(self.pin, self._gpio.HIGH)
                time.sleep(duration)
                self._gpio.output(self.pin, self._gpio.LOW)
            else:
                print("[BUZZER] beep")
                time.sleep(duration)
            time.sleep(gap)
