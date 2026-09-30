# sensors.py - reads the BH1750, the LDR and the PIR sensor
from machine import Pin, I2C, ADC
from bh1750 import BH1750

_i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)
_bh1750 = BH1750(0x23, _i2c)
_ldr = ADC(26)
_pir = Pin(15, Pin.IN)
button = Pin(14, Pin.IN, Pin.PULL_UP)


def indoor_lux():
    """Indoor light level in lux (BH1750)."""
    try:
        return round(_bh1750.measurement)
    except OSError:
        return None  # sensor not connected


def outdoor_light():
    """Outdoor light level from the LDR, 0.0 (dark) ... 1.0 (bright)."""
    return round(_ldr.read_u16() / 65535, 2)


def presence():
    """True when the PIR sensor detects movement."""
    return _pir.value() == 1
