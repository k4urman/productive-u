# World's Greatest Clock

A smart alarm clock for the **M5Stack Fire** (ESP32).

---

## Feature Map

| Feature | File | Notes |
|---|---|---|
| NTP atomic sync (auto re-sync every 6 h) | `clock.py` | Falls back to RTC if WiFi down |
| Auto DST (US rule, configurable) | `clock.py` | Any region supported via config |
| Weather glow LEDs | `leds.py` | Blue=rain, gold=clear, purple=storm… |
| Sunrise pre-alarm LED ramp | `leds.py` | Starts N min before alarm |
| LED breathe animation | `leds.py` | Slow sine-wave pulse |
| Sensory alarm (sunrise + chime preview + audio) | `alarm.py` | Full sequence |
| Snooze (Button A during alarm) | `alarm.py` | Configurable duration |
| Morning briefing (weather + calendar, TTS) | `tts.py` | Plays after dismiss |
| Internet radio (2 stations, Button A/B) | `radio.py` | Any MP3 stream |
| Ambient auto-dimming | `display.py` | ADC light sensor on Pin 36 |
| Circadian color tint | `display.py` | Warm orange at night |
| Screen auto-flip (accelerometer) | `imu.py` | Always right-side-up |
| Rotate to change mode | `imu.py` | 4 orientations = 4 modes |
| Countdown timer mode | `modes.py` | Button A=start/stop, B=reset |
| Kitchen stopwatch mode | `modes.py` | Count-up with target alarm |
| Full weather dashboard mode | `display.py` | Temp, humidity, wind |
| Home Assistant MQTT overlay | `mqtt_ha.py` | Indoor temp, AQI, doorbell |
| Hourly chimes (8-bit / Westminster) | `chime.py` | Quiet hours respected |
| Tick-tock style | `chime.py` | Via `CHIME_STYLE = "ticktock"` |
| GIF animated background | `display.py` | Pre-convert with `gif_to_frames.py` |
| Anti-aliased fonts (DejaVu) | `display.py` | Best quality in MicroPython |

---

## File Structure

```
m5stack_ultimate_clock/
├── main.py           ← Upload this (entry point + main loop)
├── config.py         ← ALL user settings live here
├── clock.py          ← NTP, DST, time helpers
├── display.py        ← All rendering, dimming, circadian
├── leds.py           ← SK6812 LED bars
├── alarm.py          ← Alarm engine, sunrise sequence
├── radio.py          ← Internet radio
├── weather.py        ← OpenWeatherMap
├── calendar_ics.py   ← Google Calendar ICS parser
├── tts.py            ← Text-to-speech (calls laptop server)
├── mqtt_ha.py        ← Home Assistant MQTT
├── imu.py            ← Accelerometer (screen flip + mode rotate)
├── chime.py          ← Hourly chimes
├── modes.py          ← Mode state machine
├── tts_server.py     ← Run on your LAPTOP (not M5Stack)
└── tools/
    └── gif_to_frames.py  ← Run on laptop to convert GIFs
```

---

## Quick Start

### 1. Flash firmware
Use [M5Burner](https://docs.m5stack.com/en/uiflow/uiflow_home_page) to flash **UIFlow v1.12+** onto the M5Stack Fire.  Enter your WiFi credentials during the flash wizard.

### 2. Edit config.py
Fill in every `YOUR_...` placeholder:

```python
WIFI_SSID        = "MyNetwork"
WIFI_PASSWORD    = "MyPassword"
ALARM_HOUR       = 7
TZ_UTC_OFFSET    = -5          # standard time (no DST)
OWM_API_KEY      = "abc123"    # openweathermap.org — free tier
OWM_CITY         = "Indianapolis,US"
GCAL_ICS_URL     = "https://calendar.google.com/calendar/ical/..."
TTS_SERVER_IP    = "192.168.1.42"   # your laptop's IP (see step 4)
```

### 3. Upload all .py files
In the UIFlow web IDE (flow.m5stack.com) switch to **Python mode**, then use the file manager to upload **all `.py` files** (not the tools/ folder, not tts_server.py).

Or with ampy:
```bash
pip install adafruit-ampy
for f in *.py; do ampy --port /dev/ttyUSB0 put $f; done
```

### 4. Start the TTS server on your laptop
```bash
pip install flask gTTS
python tts_server.py
```
Copy the IP it prints (e.g. `192.168.1.42`) into `config.py → TTS_SERVER_IP`.  Your laptop and M5Stack must be on the same WiFi.

---

## Button Reference

| Button | Clock Mode | Timer Mode | Kitchen Mode | During Alarm |
|---|---|---|---|---|
| **A** (left) | Radio 1 on/off | Start / Stop | Start / Stop | **Snooze** |
| **B** (middle) | Radio 2 on/off | Reset | Reset | **Dismiss** |
| **C** (right) | Morning briefing | — | — | **Dismiss** |

---

## Rotate to Change Mode

Hold the device still for ~1 second in each orientation:

| Physical Orientation | Mode |
|---|---|
| Normal portrait (upright) | Clock |
| 90° clockwise (landscape) | Countdown Timer |
| 180° (upside-down) | Kitchen Stopwatch |
| 90° counter-clockwise | Weather Dashboard |

---

## LED Colors (Weather Glow)

| Color | Condition |
|---|---|
| Warm gold | Clear / sunny |
| Cool grey-blue | Cloudy / overcast |
| Blue | Rain / drizzle |
| Ice white | Snow / sleet |
| Purple | Thunderstorm |
| Red | Hot day (>90°F) |
| Light blue | Cold day (<32°F) |

The LEDs slowly breathe (sine-wave pulse) by default. Disable with `LED_BREATHE_ENABLED = False`.

---

## Sensory Alarm Sequence

```
T - 10 min : LED sunrise begins (deep red ember → warm orange)
T -  2 min : Soft 2-note preview chime
T +  0 min : Full alarm audio + LED flash
             Button A → snooze (9 min by default)
             Button B/C → dismiss + morning briefing
```
Change `SUNRISE_PRE_ALARM_MINUTES` in config.py to adjust the lead time.

---

## GIF Animated Background

1. Find a looping GIF (240p, ideally 320×240 or close)
2. Convert it on your laptop:
   ```bash
   pip install Pillow
   python tools/gif_to_frames.py my_animation.gif ./frames_output/
   ```
3. Copy the `frames_output/` folder to your MicroSD card as e.g. `/sd/rain_loop/`
4. In config.py set:
   ```python
   GIF_BACKGROUND = "/sd/rain_loop"
   ```

The M5Stack blits one raw RGB565 frame per display tick (~250 ms). For smooth animation use GIFs with ≤15 fps and ≤30 frames to avoid SD read latency.

---

## Home Assistant MQTT

1. Set `MQTT_ENABLED = True` in config.py
2. Fill in `MQTT_BROKER`, `MQTT_USER`, `MQTT_PASSWORD`
3. Set the topic strings to match your HA entity state topics
4. The clock overlay will show indoor temperature, AQI, next calendar event, and a **DOORBELL** alert when your doorbell sensor fires

---

## Chime Styles

Set `CHIME_STYLE` in config.py:

| Value | Sound |
|---|---|
| `"8bit"` | Retro video-game arpeggio fanfare |
| `"westminster"` | Classic 4-note Westminster chime |
| `"ticktock"` | Alternating 800/600 Hz tick every second |
| `"none"` | Silent |

Quiet hours (no chimes) are controlled by `CHIME_QUIET_START` and `CHIME_QUIET_END`.

---

## Notes & Limitations

- **HTTPS streams**: The ESP32's TLS stack is limited. Use `http://` radio streams where possible. If a stream requires HTTPS, set up an HTTP proxy on your router or use a redirector.
- **RAM**: The ESP32 has ~200 KB free heap in MicroPython. The GIF player, MQTT, and weather are all designed to avoid large allocations. If you hit `MemoryError`, disable GIF_BACKGROUND first.
- **speaker.playMP3()**: This is the correct UIFlow v1.8 API. Passing `""` stops playback.
- **Perpetual power**: The M5Stack Fire has a 550 mAh battery. For a true always-on clock, power it via USB. For solar, wire a 5V solar panel + TP4056 charger to the USB-C port.
- **10-year battery**: Not achievable with ESP32 WiFi active. For a WiFi-free RTC-only fallback, add a DS3231 RTC module via I2C — it runs for 10+ years on a CR2032.
