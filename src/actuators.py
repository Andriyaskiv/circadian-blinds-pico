# actuators.py - stepper motor for the blind and PWM LED lamp
import time
from machine import Pin, PWM

# 28BYJ-48 half-step sequence (ULN2003 on GP10-GP13)
_SEQ = [
    (1, 0, 0, 0), (1, 1, 0, 0), (0, 1, 0, 0), (0, 1, 1, 0),
    (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 0, 1), (1, 0, 0, 1),
]
_coils = [Pin(p, Pin.OUT) for p in (10, 11, 12, 13)]
_lamp = PWM(Pin(16))
_lamp.freq(1000)


class Blind:
    def __init__(self, full_steps):
        self.full_steps = full_steps  # steps from fully closed to fully open
        self.position = 0             # 0 = closed, 100 = open
        self._phase = 0

    def _step(self, direction):
        self._phase = (self._phase + direction) % 8
        for coil, value in zip(_coils, _SEQ[self._phase]):
            coil.value(value)
        time.sleep_ms(2)

    def _release(self):
        for coil in _coils:
            coil.value(0)

    def move_to(self, position):
        position = max(0, min(100, int(position)))
        steps = (position - self.position) * self.full_steps // 100
        direction = 1 if steps > 0 else -1
        for _ in range(abs(steps)):
            self._step(direction)
        self._release()
        self.position = position
        return self.position


class Lamp:
    def __init__(self):
        self.brightness = 0

    def set(self, percent):
        self.brightness = max(0, min(100, int(percent)))
        _lamp.duty_u16(self.brightness * 65535 // 100)
        return self.brightness
