# ── WiFi ──────────────────────────────────────────────────
WIFI_SSID     = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# ── Timezone & DST ───────────────────────────────────────
TZ_UTC_OFFSET  = -5   # EST=-5, CST=-6, MST=-7, PST=-8

DST_ENABLED    = True
DST_START_MONTH  = 3
DST_START_WEEK   = 2
DST_END_MONTH    = 11
DST_END_WEEK     = 1
DST_OFFSET       = 1

# ── PC Agent (run agent_server.py on your laptop) ────────
AGENT_IP   = "192.168.1.XXX"
AGENT_PORT = 5001

# ── Pomodoro ─────────────────────────────────────────────
POMODORO_WORK_MINUTES  = 25
POMODORO_BREAK_MINUTES = 5
POMODORO_AUTO_START_ON_FLIP = True   # start work block when flipped while idle

# ── Flip-to-Track (IMU orientations → task labels) ───────
# Keys must match imu.py orientation names.
TASK_BY_ORIENTATION = {
    "portrait":          "Coding",
    "landscape_right":   "Email",
    "portrait_inverted": "Admin",
    "landscape_left":    "Meetings",
}

# ── Weather ──────────────────────────────────────────────
OWM_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
OWM_CITY    = "Indianapolis,US"
OWM_UNITS   = "imperial"

# ── Google Calendar ──────────────────────────────────────
GCAL_ICS_URL = "https://calendar.google.com/calendar/ical/YOUR_ID/basic.ics"

# ── Ticker ───────────────────────────────────────────────
TICKER_ROTATE_SECONDS = 12   # auto-cycle when idle (0 = manual only via refresh)

# ── Macro layers (Button A cycles; B/C fire actions) ─────
# Action strings are sent to agent_server.py — map them there.
MACRO_LAYERS = [
    {
        "name": "Zoom",
        "b": "zoom_mute_toggle",
        "c": "zoom_camera_toggle",
    },
    {
        "name": "Media",
        "b": "media_prev",
        "c": "media_next",
    },
    {
        "name": "Coding",
        "b": "code_run_tests",
        "c": "code_format",
    },
]

# ── Display ──────────────────────────────────────────────
AMBIENT_NIGHT_THRESHOLD = 500
SCREEN_BRIGHTNESS_DAY   = 100
SCREEN_BRIGHTNESS_NIGHT = 20
CIRCADIAN_ENABLED = False   # solid orange/green pomodoro colors read better

# Pomodoro screen colors (RGB565-ish as 0xRRGGBB)
COLOR_WORK  = 0xFF6600   # bright orange
COLOR_BREAK = 0x00CC44   # green
COLOR_IDLE  = 0x111111   # near-black background for ticker

# ── LED status (side NeoPixel bars) ──────────────────────
LED_BRIGHTNESS_MAX = 80
LED_COLOR_MIC_HOT     = (255, 0, 0)
LED_COLOR_RENDER_DONE = (255, 200, 0)
LED_COLOR_IDLE        = (0, 0, 0)

# ── Voice memos (microSD recommended) ────────────────────
MEMO_DIR          = "/sd/memos"
MEMO_SAMPLE_RATE  = 8000
MEMO_POWER_HOLD_MS = 600    # hold red power button this long to record

# ── Home Assistant / MQTT (optional ticker extras) ───────
MQTT_ENABLED  = False
MQTT_BROKER   = "192.168.1.XXX"
MQTT_PORT     = 1883
MQTT_USER     = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "productive_u"

MQTT_TOPIC_INDOOR_TEMP  = "homeassistant/sensor/indoor_temp/state"
MQTT_TOPIC_AQI          = "homeassistant/sensor/outdoor_aqi/state"
MQTT_TOPIC_DOORBELL     = "homeassistant/binary_sensor/doorbell/state"
MQTT_TOPIC_NEXT_EVENT   = "homeassistant/sensor/next_calendar_event/state"
