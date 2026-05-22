# ── WiFi ──────────────────────────────────────────────────
WIFI_SSID     = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# ── Timezone & DST ───────────────────────────────────────
# Base UTC offset WITHOUT DST (standard time)
TZ_UTC_OFFSET  = -5   # EST=-5, CST=-6, MST=-7, PST=-8

# DST rule — US default (2nd Sun Mar → 1st Sun Nov, +1 hr)
DST_ENABLED    = True
DST_START_MONTH  = 3    # March
DST_START_WEEK   = 2    # 2nd Sunday
DST_END_MONTH    = 11   # November
DST_END_WEEK     = 1    # 1st Sunday
DST_OFFSET       = 1    # hours to add during DST

# ── Alarm ────────────────────────────────────────────────
ALARM_HOUR     = 7
ALARM_MINUTE   = 0
ALARM_ENABLED  = True
SNOOZE_MINUTES = 9

# Sensory wake-up: sunrise LED begins this many minutes before alarm
SUNRISE_PRE_ALARM_MINUTES = 10

# Optional: URL to MP3 hosted on TTS server (or None for buzzer)
ALARM_AUDIO_URL = None   # e.g. "http://192.168.1.42:5001/alarm.mp3"

# ── TTS Server ───────────────────────────────────────────
TTS_SERVER_IP   = "192.168.1.XXX"   # your computer's local IP
TTS_SERVER_PORT = 5001

# ── Weather ──────────────────────────────────────────────
OWM_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
OWM_CITY    = "Indianapolis,US"
OWM_UNITS   = "imperial"   # "imperial" or "metric"

# ── Google Calendar ──────────────────────────────────────
GCAL_ICS_URL = "https://calendar.google.com/calendar/ical/YOUR_ID/basic.ics"

# ── Radio ────────────────────────────────────────────────
RADIO_STATION_1_URL  = "http://ice1.somafm.com/groovesalad-128-mp3"
RADIO_STATION_1_NAME = "Groove Salad"
RADIO_STATION_2_URL  = "http://ice1.somafm.com/seventies-128-mp3"
RADIO_STATION_2_NAME = "70s Hits"

# ── Home Assistant / MQTT ────────────────────────────────
MQTT_ENABLED  = False
MQTT_BROKER   = "192.168.1.XXX"   # HA server IP
MQTT_PORT     = 1883
MQTT_USER     = ""
MQTT_PASSWORD = ""
MQTT_CLIENT_ID = "m5stack_clock"

# Topics to subscribe to (set empty string to disable)
MQTT_TOPIC_INDOOR_TEMP  = "homeassistant/sensor/indoor_temp/state"
MQTT_TOPIC_AQI          = "homeassistant/sensor/outdoor_aqi/state"
MQTT_TOPIC_DOORBELL     = "homeassistant/binary_sensor/doorbell/state"
MQTT_TOPIC_NEXT_EVENT   = "homeassistant/sensor/next_calendar_event/state"

# ── Display ──────────────────────────────────────────────
# Ambient light sensor threshold (0-4095, M5Stack Fire built-in ADC)
# Below this value = night → dim screen
AMBIENT_NIGHT_THRESHOLD = 500
SCREEN_BRIGHTNESS_DAY   = 100   # 0-100
SCREEN_BRIGHTNESS_NIGHT = 20

# Circadian color temperature: warm (orange tint) at night, cool (white) at day
CIRCADIAN_ENABLED = True

# GIF background file on SD card (None to disable)
GIF_BACKGROUND = None   # e.g. "/sd/rain_loop.gif"

# ── Chime ────────────────────────────────────────────────
CHIME_ENABLED      = True
CHIME_STYLE        = "8bit"   # "8bit" | "westminster" | "ticktock" | "none"
CHIME_QUIET_START  = 22   # hour: no chimes after this (24h)
CHIME_QUIET_END    = 7    # hour: chimes resume after this

# ── LED bars ─────────────────────────────────────────────
LED_BRIGHTNESS_MAX  = 80   # 0-255, cap to avoid blinding yourself
LED_BREATHE_ENABLED = True

# Weather glow colors (R, G, B)
LED_COLOR_CLEAR  = (255, 200,  80)   # warm gold
LED_COLOR_CLOUDY = (180, 180, 220)   # cool grey-blue
LED_COLOR_RAIN   = ( 30,  80, 255)   # blue
LED_COLOR_SNOW   = (200, 220, 255)   # ice white
LED_COLOR_STORM  = (160,   0, 220)   # purple
LED_COLOR_HOT    = (255,  30,   0)   # red  (>90F / 32C)
LED_COLOR_COLD   = ( 80, 160, 255)   # light blue (<32F / 0C)

# Sunrise alarm colors (start → end)
LED_SUNRISE_START = (20,  5,  0)   # deep red ember
LED_SUNRISE_END   = (255, 160, 40) # warm sunrise orange
