import m5stack
import m5ui
import utime
import ntptime
import network
import urequests
import ujson
import machine
from m5stack import lcd, btnA, btnB, btnC, speaker
from m5ui import setScreenColor, M5TextBox, M5Rect

# ─────────────────────────────────────────────
#  USER CONFIGURATION  (edit these values)
# ─────────────────────────────────────────────
WIFI_SSID     = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# Alarm time (24-hour)
ALARM_HOUR   = 7
ALARM_MINUTE = 0

# Timezone offset from UTC in hours (e.g. -5 for EST, -6 for CST)
TZ_OFFSET_HOURS = -5

# Weather — OpenWeatherMap free API
OWM_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
OWM_CITY    = "Indianapolis,US"   # or use lat/lon below
# OWM_LAT   = 39.9784
# OWM_LON   = -86.1180

# Google Calendar — public ICS feed URL (File > Settings > Get shareable link, choose ICS)
# For private calendars, generate a secret address in Calendar settings
GCAL_ICS_URL = "https://calendar.google.com/calendar/ical/YOUR_CALENDAR_ID/basic.ics"

# Radio streams (MP3 / AAC internet radio URLs)
RADIO_STATION_1_URL  = "http://ice1.somafm.com/groovesalad-128-mp3"   # SomaFM Groove Salad
RADIO_STATION_1_NAME = "Groove Salad"
RADIO_STATION_2_URL  = "http://ice1.somafm.com/seventies-128-mp3"      # SomaFM 70s Hits
RADIO_STATION_2_NAME = "70s Hits"

# Alarm audio — path to a .wav file on the SD card, or use buzzer tones
# Set to None to use the built-in buzzer melody instead
ALARM_AUDIO_FILE = "/sd/alarm.wav"   # None = buzzer

# Snooze duration in minutes
SNOOZE_MINUTES = 9

# TTS service: "google" (free, needs internet) or "espeak" (offline, lower quality)
TTS_SERVICE = "google"   # only "google" implemented here

# ─────────────────────────────────────────────
#  GLOBALS
# ─────────────────────────────────────────────
wlan          = None
alarm_active  = False
radio_playing = None   # None | 1 | 2
snooze_until  = None   # utime.time() value
weather_text  = ""
calendar_text = ""

# ─────────────────────────────────────────────
#  WIFI
# ─────────────────────────────────────────────
def connect_wifi():
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        lcd_status("Connecting WiFi…")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            utime.sleep(1)
            timeout -= 1
    if wlan.isconnected():
        lcd_status("WiFi OK: " + wlan.ifconfig()[0])
    else:
        lcd_status("WiFi FAILED — offline mode")

# ─────────────────────────────────────────────
#  NTP / CLOCK
# ─────────────────────────────────────────────
def sync_time():
    try:
        ntptime.settime()   # sets RTC to UTC
        lcd_status("Time synced (NTP)")
    except Exception as e:
        lcd_status("NTP sync failed: " + str(e))

def local_time():
    """Return local time tuple accounting for TZ offset."""
    t = utime.time() + TZ_OFFSET_HOURS * 3600
    return utime.localtime(t)

def time_str():
    lt = local_time()
    return "{:02d}:{:02d}:{:02d}".format(lt[3], lt[4], lt[5])

def date_str():
    lt = local_time()
    days   = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    months = ["","Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    return "{} {} {}".format(days[lt[6]], lt[2], months[lt[1]])

# ─────────────────────────────────────────────
#  WEATHER
# ─────────────────────────────────────────────
def fetch_weather():
    global weather_text
    try:
        url = ("http://api.openweathermap.org/data/2.5/weather"
               "?q={}&appid={}&units=imperial".format(OWM_CITY, OWM_API_KEY))
        r   = urequests.get(url, timeout=10)
        d   = ujson.loads(r.text)
        r.close()
        desc  = d["weather"][0]["description"].capitalize()
        temp  = round(d["main"]["temp"])
        feels = round(d["main"]["feels_like"])
        humidity = d["main"]["humidity"]
        weather_text = (
            "Weather in {}. {}. "
            "{} degrees Fahrenheit, feels like {}. "
            "Humidity {}%.".format(
                OWM_CITY.split(",")[0], desc,
                temp, feels, humidity))
        lcd_status("Weather fetched")
    except Exception as e:
        weather_text = "Weather unavailable."
        lcd_status("Weather error: " + str(e))

# ─────────────────────────────────────────────
#  GOOGLE CALENDAR (ICS parser — minimal)
# ─────────────────────────────────────────────
def fetch_calendar():
    global calendar_text
    try:
        r    = urequests.get(GCAL_ICS_URL, timeout=15)
        ics  = r.text
        r.close()
        events = parse_ics_today(ics)
        if events:
            parts = ["You have {} event{} today. ".format(
                len(events), "s" if len(events) > 1 else "")]
            for ev in events[:5]:   # speak max 5 events
                parts.append(ev)
            calendar_text = " ".join(parts)
        else:
            calendar_text = "No calendar events today."
        lcd_status("Calendar fetched")
    except Exception as e:
        calendar_text = "Calendar unavailable."
        lcd_status("Calendar error: " + str(e))

def parse_ics_today(ics_text):
    """Tiny ICS parser — returns list of summary strings for today's events."""
    lt    = local_time()
    today = "{:04d}{:02d}{:02d}".format(lt[0], lt[1], lt[2])
    events = []
    in_event = False
    summary  = ""
    dtstart  = ""
    for line in ics_text.split("\n"):
        line = line.strip()
        if line == "BEGIN:VEVENT":
            in_event = True
            summary  = ""
            dtstart  = ""
        elif line == "END:VEVENT":
            if in_event and today in dtstart:
                # Extract HH:MM from dtstart like 20240513T090000Z
                try:
                    t_part = dtstart.split("T")[1][:4]
                    h = t_part[:2]
                    m = t_part[2:]
                    # Adjust for TZ (rough)
                    hour = (int(h) + TZ_OFFSET_HOURS) % 24
                    events.append("{} at {:02d}:{}.".format(summary, hour, m))
                except Exception:
                    events.append(summary + ".")
            in_event = False
        elif in_event:
            if line.startswith("SUMMARY:"):
                summary = line[8:]
            elif line.startswith("DTSTART"):
                dtstart = line.split(":")[-1]
    return events

# ─────────────────────────────────────────────
#  TEXT-TO-SPEECH  (Google Translate TTS)
# ─────────────────────────────────────────────
def tts_speak(text):
    """
    Streams Google Translate TTS audio to the M5Stack speaker.
    Splits long text into ≤200-char chunks.
    NOTE: Google Translate TTS is unofficial; for production use
    a proper TTS API (ElevenLabs, AWS Polly, etc.) via an HTTPS proxy.
    """
    stop_radio()
    chunks = split_text(text, 200)
    for chunk in chunks:
        if not chunk.strip():
            continue
        try:
            encoded = chunk.replace(" ", "%20").replace(",", "%2C") \
                          .replace(".", "%2E").replace("'", "%27")
            url = ("http://translate.google.com/translate_tts"
                   "?ie=UTF-8&client=tw-ob&tl=en&q={}".format(encoded))
            # Stream audio bytes to speaker
            speaker.playCloudMP3(url)      # UIFlow built-in cloud MP3 player
            utime.sleep_ms(300)
        except Exception as e:
            lcd_status("TTS err: " + str(e))

def split_text(text, max_len):
    words  = text.split(" ")
    chunks = []
    cur    = ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_len:
            cur = cur + " " + w if cur else w
        else:
            chunks.append(cur)
            cur = w
    if cur:
        chunks.append(cur)
    return chunks

# ─────────────────────────────────────────────
#  MORNING BRIEFING
# ─────────────────────────────────────────────
def morning_briefing():
    lcd_status("Fetching briefing…")
    fetch_weather()
    fetch_calendar()
    lt   = local_time()
    h    = lt[3]
    if   h < 12: greeting = "Good morning!"
    elif h < 17: greeting = "Good afternoon!"
    else:        greeting = "Good evening!"

    script = (
        "{} Today is {}. The time is {}. "
        "{} "
        "{}"
    ).format(
        greeting,
        date_str(),
        time_str(),
        weather_text,
        calendar_text,
    )
    lcd_status("Speaking briefing…")
    tts_speak(script)
    lcd_status("Briefing done.")

# ─────────────────────────────────────────────
#  ALARM
# ─────────────────────────────────────────────
def check_alarm():
    global alarm_active, snooze_until
    if alarm_active:
        return
    lt  = local_time()
    now = utime.time()
    # Check snooze
    if snooze_until and now < snooze_until:
        return
    snooze_until = None
    if lt[3] == ALARM_HOUR and lt[4] == ALARM_MINUTE:
        trigger_alarm()

def trigger_alarm():
    global alarm_active
    alarm_active = True
    stop_radio()
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.RED)
    lcd.text(lcd.CENTER, 80, "WAKE UP!")
    lcd.setTextColor(lcd.WHITE)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.text(lcd.CENTER, 140, "A=Snooze  B=Dismiss  C=Radio2")
    play_alarm_sound()

def play_alarm_sound():
    if ALARM_AUDIO_FILE:
        try:
            speaker.playWAV(ALARM_AUDIO_FILE, volume=8)
            return
        except Exception:
            pass
    # Fallback: buzzer melody
    notes = [659, 659, 0, 659, 0, 523, 659, 0, 784]
    for n in notes:
        if n:
            speaker.tone(n, 150)
        utime.sleep_ms(200)

def snooze_alarm():
    global alarm_active, snooze_until
    alarm_active = False
    speaker.stop()
    snooze_until = utime.time() + SNOOZE_MINUTES * 60
    lcd_status("Snoozed {}min".format(SNOOZE_MINUTES))

def dismiss_alarm():
    global alarm_active, snooze_until
    alarm_active = False
    snooze_until = None
    speaker.stop()
    morning_briefing()   # speak the morning summary after dismissing

# ─────────────────────────────────────────────
#  RADIO
# ─────────────────────────────────────────────
def play_radio(station):
    global radio_playing
    stop_radio()
    url  = RADIO_STATION_1_URL  if station == 1 else RADIO_STATION_2_URL
    name = RADIO_STATION_1_NAME if station == 1 else RADIO_STATION_2_NAME
    try:
        speaker.playCloudMP3(url)
        radio_playing = station
        lcd_status("Radio: " + name)
    except Exception as e:
        lcd_status("Radio err: " + str(e))

def stop_radio():
    global radio_playing
    try:
        speaker.stop()
    except Exception:
        pass
    radio_playing = None

def toggle_radio(station):
    if radio_playing == station:
        stop_radio()
        lcd_status("Radio off")
    else:
        play_radio(station)

# ─────────────────────────────────────────────
#  DISPLAY
# ─────────────────────────────────────────────
def draw_clock_face():
    if alarm_active:
        return
    lcd.clear()
    # Time
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.WHITE)
    lcd.text(lcd.CENTER, 10, time_str())
    # Date
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.CYAN)
    lcd.text(lcd.CENTER, 65, date_str())
    # Alarm indicator
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(lcd.YELLOW)
    lcd.text(lcd.CENTER, 100,
             "Alarm {:02d}:{:02d}".format(ALARM_HOUR, ALARM_MINUTE))
    # Radio status
    if radio_playing:
        name = RADIO_STATION_1_NAME if radio_playing == 1 else RADIO_STATION_2_NAME
        lcd.setTextColor(lcd.GREEN)
        lcd.text(lcd.CENTER, 125, "♫ " + name)
    # Snooze indicator
    global snooze_until
    if snooze_until:
        remaining = max(0, snooze_until - utime.time()) // 60
        lcd.setTextColor(lcd.ORANGE)
        lcd.text(lcd.CENTER, 150, "Snooze: {}min left".format(remaining))
    # Button hints
    lcd.setTextColor(0x888888)
    lcd.font(lcd.FONT_Default)
    lcd.text(10,   220, "Radio1")
    lcd.text(130,  220, "Radio2")
    lcd.text(245,  220, "Brief")

def lcd_status(msg):
    print(msg)   # also to serial console
    if not alarm_active:
        lcd.font(lcd.FONT_Default)
        lcd.setTextColor(lcd.WHITE)
        # Print in status bar area
        lcd.rect(0, 195, 320, 20, lcd.BLACK, lcd.BLACK)
        lcd.text(5, 197, msg[:50])

# ─────────────────────────────────────────────
#  BUTTON HANDLERS
# ─────────────────────────────────────────────
def on_btn_a():
    if alarm_active:
        snooze_alarm()
    else:
        toggle_radio(1)

def on_btn_b():
    if alarm_active:
        dismiss_alarm()
    else:
        toggle_radio(2)

def on_btn_c():
    if alarm_active:
        dismiss_alarm()
    else:
        # Long-press or single press → morning briefing on demand
        morning_briefing()

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    setScreenColor(0x000000)
    lcd.clear()
    lcd_status("Booting…")

    connect_wifi()
    sync_time()

    btnA.wasPressed(on_btn_a)
    btnB.wasPressed(on_btn_b)
    btnC.wasPressed(on_btn_c)

    lcd_status("Ready.")
    last_clock_draw = 0
    last_alarm_check = 0

    while True:
        now = utime.ticks_ms()

        # Redraw clock every second
        if utime.ticks_diff(now, last_clock_draw) >= 1000:
            draw_clock_face()
            last_clock_draw = now

        # Check alarm every 30 seconds
        if utime.ticks_diff(now, last_alarm_check) >= 30000:
            check_alarm()
            last_alarm_check = now

        # Keep alarm sound looping while active
        if alarm_active:
            play_alarm_sound()
            utime.sleep_ms(2000)

        utime.sleep_ms(50)

main()
