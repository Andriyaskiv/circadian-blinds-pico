# Circadian Blinds – Smart Home Controller for Raspberry Pi Pico W

*Automatic window blinds and room lighting that follow your daily rhythm.*

**Circadian Blinds** is a small smart home system built on the **Raspberry Pi Pico W** and **MicroPython**.
It opens the blinds gradually in the morning, closes them in the evening and dims the room light at bedtime.
Decisions are based on indoor and outdoor light levels, the local weather forecast and a user-defined sleep schedule.
The system can be controlled from any browser on the home network, and it sends notifications to a Discord channel.

**Repository:** <https://github.com/Andriyaskiv/circadian-blinds-pico>  
**Online version of this README:** <https://andriyaskiv.github.io/circadian-blinds-pico/>

> **Note:** This project was made as a course project for an IoT / smart home course.
> It is a prototype and it is not meant to control mains-powered devices without proper safety measures.

---

## Table of Contents

1. [Features](#features)
2. [Hardware](#hardware)
3. [Prerequisites and Dependencies](#prerequisites-and-dependencies)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Usage](#usage)
7. [Project Structure](#project-structure)
8. [Roadmap](#roadmap)
9. [Maintainer](#maintainer)
10. [License](#license)

## Features

- **Sunrise routine** – the blinds open step by step when it gets light outside or at the wake-up time.
- **Night routine** – at bedtime the blinds close and the LED lamp dims slowly to 0 %.
- **Weather awareness** – the forecast from the [Open-Meteo API](https://open-meteo.com/) is checked every 30 minutes.
  - On very sunny and hot days the blinds stay half-closed.
  - On cloudy days the lamp brightness is increased.
- **Web dashboard** – a simple REST API and web page to see sensor values and control the blinds manually.
- **Remote notifications** – important events are sent to Discord through a webhook.

## Hardware

| Component | Type | Pico W pin | Purpose |
|---|---|---|---|
| BH1750 light sensor | Sensor (I²C) | GP4 (SDA), GP5 (SCL) | Indoor light level in lux |
| LDR + 10 kΩ resistor | Sensor (analog) | GP26 (ADC0) | Outdoor light level |
| HC-SR501 PIR sensor | Sensor (digital) | GP15 | Detects if someone is in the room |
| 28BYJ-48 stepper + ULN2003 | Actuator | GP10–GP13 | Rolls the blind up and down |
| LED strip + MOSFET | Actuator (PWM) | GP16 | Dimmable room light |
| Push button | Input | GP14 | Manual open / close |

## Prerequisites and Dependencies

Before installing, make sure you have:

- A **Raspberry Pi Pico W** with [MicroPython firmware](https://micropython.org/download/RPI_PICO_W/) v1.23 or newer
- A 2.4 GHz Wi-Fi network
- A computer with **Python 3.10+**
- [`mpremote`](https://docs.micropython.org/en/latest/reference/mpremote.html) for copying files to the board
- A Discord server where you can create a webhook (optional)

The project uses the following **external libraries**:

| Library | Version | Used for |
|---|---|---|
| [`microdot`](https://github.com/miguelgrinberg/microdot) | 2.x | Web server and REST API |
| [`bh1750`](https://github.com/flrrth/pico-bh1750) | latest | Driver for the BH1750 light sensor |
| `requests` | built-in (Pico W firmware) | HTTP requests to Open-Meteo and Discord |
| `ntptime` | built-in | Time synchronisation over NTP |

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Andriyaskiv/circadian-blinds-pico.git
   cd circadian-blinds-pico
   ```

2. Install `mpremote` on your computer:

   ```bash
   pip install mpremote
   ```

3. Connect the Pico W with a USB cable and install the libraries on the board:

   ```bash
   mpremote mip install --target /lib/microdot \
       github:miguelgrinberg/microdot/src/microdot/__init__.py \
       github:miguelgrinberg/microdot/src/microdot/microdot.py

   mpremote mip install --target /lib/bh1750 \
       github:flrrth/pico-bh1750/bh1750/__init__.py \
       github:flrrth/pico-bh1750/bh1750/bh1750.py
   ```

4. Create your `config.json` (see [Configuration](#configuration)) and copy the project files to the board:

   ```bash
   mpremote cp src/*.py :
   mpremote mkdir web
   mpremote cp src/web/index.html :web/index.html
   mpremote cp config.json :
   ```

5. Reset the board. The program starts automatically from `main.py`.

## Configuration

All settings are stored in `config.json`. Copy [`config.example.json`](https://github.com/Andriyaskiv/circadian-blinds-pico/blob/main/config.example.json) and edit the values:

```json
{
  "wifi_ssid": "MyHomeWiFi",
  "wifi_password": "secret",
  "latitude": 60.98,
  "longitude": 25.66,
  "utc_offset_hours": 3,
  "wake_up_time": "07:30",
  "bed_time": "23:00",
  "blind_steps": 8192,
  "discord_webhook": "https://discord.com/api/webhooks/..."
}
```

> **Warning:** Never commit your real `config.json` to Git. It contains your Wi-Fi password and webhook URL.

## Usage

After boot, the Pico W prints its IP address to the serial console (for example with `mpremote repl`):

```text
[wifi] connected, IP = 192.168.1.42
[web] dashboard running on http://192.168.1.42/
```

Open the address in a browser to see the dashboard. You can also use the REST API directly:

```bash
# Read all sensor values
curl http://192.168.1.42/api/status

# Open the blinds to 75 %
curl -X POST http://192.168.1.42/api/blinds -d '{"position": 75}'

# Set the lamp to 60 %
curl -X POST http://192.168.1.42/api/lamp -d '{"brightness": 60}'

# Turn on night mode immediately
curl -X POST http://192.168.1.42/api/mode -d '{"mode": "night"}'
```

Example response of `/api/status`:

```json
{
  "indoor_lux": 312,
  "outdoor_light": 0.64,
  "presence": true,
  "blinds_position": 75,
  "lamp_brightness": 40,
  "weather": "partly cloudy",
  "mode": "auto"
}
```

## Project Structure

```text
circadian-blinds-pico/
├── src/
│   ├── main.py          # Starts Wi-Fi, web server and scheduler
│   ├── sensors.py       # BH1750, LDR and PIR readings
│   ├── actuators.py     # Stepper motor and PWM lamp control
│   ├── automations.py   # Sunrise, night and weather rules
│   ├── notifier.py      # Discord webhook messages
│   └── web/index.html   # Dashboard page
├── docs/index.html      # HTML version of this README (GitHub Pages)
├── config.example.json
├── LICENSE
└── README.md
```

## Roadmap

- [x] Read light sensors and PIR
- [x] Control stepper motor and LED dimming
- [x] Sunrise and night automations
- [x] Discord notifications
- [ ] Limit switch for blind calibration
- [ ] Support for more than one window

## Maintainer

This project is maintained by **Andriy Yaskiv**, exchange student in Industrial Information Technology at LAB University of Applied Sciences.

- GitHub: [@Andriyaskiv](https://github.com/Andriyaskiv)
- Issues and suggestions: please open an [issue](https://github.com/Andriyaskiv/circadian-blinds-pico/issues).

## License

Distributed under the **MIT License**. See [`LICENSE`](https://github.com/Andriyaskiv/circadian-blinds-pico/blob/main/LICENSE) for more information.
