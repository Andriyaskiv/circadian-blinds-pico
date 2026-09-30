# automations.py - sunrise, night and weather rules
import asyncio
import time
import notifier

try:
    import requests
except ImportError:
    import urequests as requests

WEATHER_URL = ("https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               "&current=temperature_2m,cloud_cover")


class Automations:
    def __init__(self, cfg, blind, lamp, sensors):
        self.cfg = cfg
        self.blind = blind
        self.lamp = lamp
        self.sensors = sensors
        self.mode = "auto"           # auto | night | manual
        self.weather = "unknown"
        self.temperature = None
        self.cloud_cover = None
        self._last_day_done = None   # avoids running a routine twice a day
        self._last_night_done = None

    # ---------- helpers ----------
    def local_time(self):
        t = time.localtime(time.time() + int(self.cfg.get("utc_offset_hours", 0)) * 3600)
        return t[2], t[3] * 60 + t[4]  # (day of month, minutes since midnight)

    @staticmethod
    def _minutes(hhmm):
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    # ---------- weather ----------
    def update_weather(self):
        url = WEATHER_URL.format(lat=self.cfg["latitude"], lon=self.cfg["longitude"])
        try:
            r = requests.get(url)
            current = r.json()["current"]
            r.close()
            self.temperature = current["temperature_2m"]
            self.cloud_cover = current["cloud_cover"]
            if self.cloud_cover < 25:
                self.weather = "sunny"
            elif self.cloud_cover < 70:
                self.weather = "partly cloudy"
            else:
                self.weather = "cloudy"
        except Exception as e:
            print("[weather] error:", e)

    # ---------- routines ----------
    async def sunrise(self):
        target = 100
        if self.weather == "sunny" and (self.temperature or 0) > 25:
            target = 50  # keep the room cool on hot sunny days
        for pos in range(self.blind.position, target + 1, 10):
            self.blind.move_to(pos)
            await asyncio.sleep(30)  # open slowly, like a real sunrise
        self.blind.move_to(target)
        notifier.send("Good morning! Blinds opened to {} %.".format(target))

    async def night(self):
        self.blind.move_to(0)
        for level in range(self.lamp.brightness, -1, -5):
            self.lamp.set(level)
            await asyncio.sleep(20)  # slow dimming before sleep
        self.lamp.set(0)
        notifier.send("Night routine done: blinds closed and light off.")

    def adjust_lamp(self):
        """Keep the room bright enough while someone is in it."""
        if not self.sensors.presence():
            return
        lux = self.sensors.indoor_lux()
        if lux is None:
            return
        wanted = 70 if self.weather == "cloudy" else 50
        if lux < 150 and self.lamp.brightness < wanted:
            self.lamp.set(wanted)
        elif lux > 400 and self.lamp.brightness > 0:
            self.lamp.set(0)

    async def tick(self):
        """Called every minute by the scheduler in main.py."""
        if self.mode == "manual":
            return
        day, now = self.local_time()
        wake = self._minutes(self.cfg["wake_up_time"])
        bed = self._minutes(self.cfg["bed_time"])

        if now >= bed or self.mode == "night":
            if self._last_night_done != day:
                self._last_night_done = day
                await self.night()
            return

        bright_outside = self.sensors.outdoor_light() > 0.4
        if now >= wake and self._last_day_done != day and (bright_outside or now >= wake + 30):
            self._last_day_done = day
            await self.sunrise()

        self.adjust_lamp()
