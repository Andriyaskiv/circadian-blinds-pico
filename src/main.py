# main.py - Circadian Blinds entry point
import asyncio
import json
import time

import network
import ntptime
from microdot import Microdot, send_file

import sensors
import notifier
from actuators import Blind, Lamp
from automations import Automations

with open("config.json") as f:
    cfg = json.load(f)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(cfg["wifi_ssid"], cfg["wifi_password"])
    for _ in range(30):
        if wlan.isconnected():
            break
        time.sleep(1)
    if not wlan.isconnected():
        raise RuntimeError("Wi-Fi connection failed")
    ip = wlan.ifconfig()[0]
    print("[wifi] connected, IP =", ip)
    return ip


ip = connect_wifi()
try:
    ntptime.settime()
except Exception as e:
    print("[ntp] error:", e)

notifier.setup(cfg.get("discord_webhook"))
blind = Blind(cfg.get("blind_steps", 8192))
lamp = Lamp()
auto = Automations(cfg, blind, lamp, sensors)
app = Microdot()


# ---------------- REST API ----------------
@app.get("/")
async def index(request):
    return send_file("web/index.html")


@app.get("/api/status")
async def status(request):
    return {
        "indoor_lux": sensors.indoor_lux(),
        "outdoor_light": sensors.outdoor_light(),
        "presence": sensors.presence(),
        "blinds_position": blind.position,
        "lamp_brightness": lamp.brightness,
        "weather": auto.weather,
        "mode": auto.mode,
    }


@app.post("/api/blinds")
async def set_blinds(request):
    data = request.json or {}
    auto.mode = "manual"
    return {"blinds_position": blind.move_to(data.get("position", 0))}


@app.post("/api/lamp")
async def set_lamp(request):
    data = request.json or {}
    auto.mode = "manual"
    return {"lamp_brightness": lamp.set(data.get("brightness", 0))}


@app.post("/api/mode")
async def set_mode(request):
    mode = (request.json or {}).get("mode", "auto")
    if mode not in ("auto", "night", "manual"):
        return {"error": "mode must be auto, night or manual"}, 400
    auto.mode = mode
    notifier.send("Mode changed to " + mode)
    return {"mode": auto.mode}


# ---------------- background tasks ----------------
async def scheduler():
    counter = 0
    while True:
        if counter % 30 == 0:
            auto.update_weather()  # every 30 minutes
        await auto.tick()
        counter += 1
        await asyncio.sleep(60)


async def button_watch():
    """Push button toggles the blind between open and closed."""
    while True:
        if sensors.button.value() == 0:
            auto.mode = "manual"
            blind.move_to(0 if blind.position > 50 else 100)
            await asyncio.sleep(1)
        await asyncio.sleep_ms(50)


async def run():
    print("[web] dashboard running on http://{}/".format(ip))
    notifier.send("Circadian Blinds started at http://{}/".format(ip))
    asyncio.create_task(scheduler())
    asyncio.create_task(button_watch())
    await app.start_server(port=80)


asyncio.run(run())
