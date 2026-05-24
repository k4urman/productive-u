# Productive-U

A desk productivity sidecar for the **M5Stack Fire** (ESP32): Pomodoro timer, flip-to-track tasks, glanceable ticker, PC macro pad, status LEDs, and voice memos.

---

## Features

| Feature | Module | Notes |
|---|---|---|
| Pomodoro (orange work / green break) | `pomodoro.py` | Dedicated full-screen timer |
| Flip-to-track tasks | `imu.py`, `tasks.py` | 4 orientations → Coding / Email / Admin / Meetings |
| 3-button macro layers | `macros.py`, `agent.py` | WiFi → `agent_server.py` on your PC |
| Zero-distraction ticker | `ticker.py` | Calendar, weather, clock (auto-rotates) |
| Status LED bars | `leds.py` | Mic-hot red, render-done yellow pulse |
| Voice memos | `voice_memo.py` | Hold red power button → `.wav` on microSD |

---

## File Structure

```
productive-u/
├── main.py            ← Entry point (upload to M5Stack)
├── config.py          ← WiFi, agent IP, pomodoro, tasks, macros
├── pomodoro.py
├── tasks.py
├── macros.py
├── agent.py           ← HTTP client to PC
├── ticker.py
├── display.py
├── imu.py
├── leds.py
├── voice_memo.py
├── clock.py
├── calendar_ics.py
├── weather.py
├── mqtt_ha.py         ← Optional Home Assistant overlay
├── agent_server.py    ← Run on your laptop (not uploaded)
└── tools/
    └── gif_to_frames.py
```

**Legacy (removed):** alarm, chime, radio, modes, TTS briefing — no longer used.

---

## Quick Start

### 1. Flash firmware

Use [M5Burner](https://docs.m5stack.com/en/uiflow/uiflow_home_page) to flash **UIFlow v1.12+** on the M5Stack Fire and set WiFi during the wizard.

### 2. Edit `config.py`

```python
WIFI_SSID     = "MyNetwork"
WIFI_PASSWORD = "MyPassword"
AGENT_IP      = "192.168.1.42"   # laptop IP (see step 3)
OWM_API_KEY   = "..."
GCAL_ICS_URL  = "https://calendar.google.com/calendar/ical/.../basic.ics"
```

### 3. Start the PC agent

```bash
pip install flask
python agent_server.py
```

Copy the printed IP into `AGENT_IP` in `config.py`. Map macro action strings in `agent_server.py` → `_run_macro()`.

### 4. Upload firmware files

In UIFlow Python mode, upload **all `.py` files** in the project root except `agent_server.py` and `tools/`.

Or with ampy:

```bash
pip install adafruit-ampy
for f in *.py; do ampy --port COM3 put $f; done
```

### 5. Voice memos (optional)

Insert a **microSD** card. Memos save to `/sd/memos/`. Create the folder if needed, or let the device create it on first record.

---

## Controls

### Screen

| State | What you see |
|---|---|
| Pomodoro active | Large countdown, orange (work) or green (break) |
| Idle | Ticker: next calendar event, weather, or time |

### Buttons (idle — no Pomodoro running)

| Button | Action |
|---|---|
| **A** | Cycle macro layer (Zoom → Media → Coding) |
| **B** | Macro action B for current layer |
| **C** | Macro action C for current layer |

### Buttons (Pomodoro active)

| Button | Action |
|---|---|
| **A** | Cycle macro layer |
| **B** | Pause / resume |
| **C** | Skip phase (work → break → work) |

### IMU — flip to track

Hold the device on each side ~1 second:

| Orientation | Default task |
|---|---|
| Portrait | Coding |
| Landscape right | Email |
| Upside-down | Admin |
| Landscape left | Meetings |

Edit labels in `config.py` → `TASK_BY_ORIENTATION`. Flipping can auto-start a work Pomodoro if `POMODORO_AUTO_START_ON_FLIP = True`.

### Power button — voice memo

**Hold** the red power button (~600 ms) to record; **release** to save WAV to microSD. Avoid double-clicking (that powers off the device).

---

## PC Agent API

| Endpoint | Method | Body / params |
|---|---|---|
| `/macro` | POST | `{"action": "zoom_mute_toggle", "layer": "Zoom"}` |
| `/track` | POST | `{"category": "Coding", "seconds": 120}` |
| `/status` | GET | Returns `mic_hot`, `render_done` |
| `/status/ack` | POST | Clears `render_done` after LED pulse |
| `/track/log` | GET | Cumulative seconds per category |

Test LEDs in a browser: `http://<agent-ip>:5001/status?mic_hot=1`

---

## Macro layers

Edit `MACRO_LAYERS` in `config.py`. Action names must match handlers you add in `agent_server.py` (`_run_macro`). Examples: `zoom_mute_toggle`, `media_next`, `code_run_tests`.

---

## Notes

- **HTTPS:** Calendar ICS and weather may need HTTP URLs or a PC proxy if TLS fails on-device.
- **RAM:** Disable MQTT if you hit `MemoryError`.
- **Power:** Keep USB power for always-on desk use; WiFi drains the 500 mAh battery quickly.
- **Agent:** Macro actions are logged by default; wire real hotkeys with `pynput`, AutoHotkey, or shell commands on your OS.
