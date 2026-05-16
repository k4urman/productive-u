"""
M5Stack Fire Alarm Clock - Fixed for UIFlow v1.8
"""

from m5stack import *
from m5ui import *
from uiflow import *
import urequests
import ntptime
import utime
import ujson

# ─────────────────────────────────────────────
#  USER CONFIGURATION
# ─────────────────────────────────────────────
WIFI_SSID     = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

ALARM_HOUR   = 7
ALARM_MINUTE = 0
TZ_OFFSET_HOURS = -5   # EST=-5, CST=-6, MST=-7, PST=-8
SNOOZE_MINUTES  = 9

OWM_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
OWM_CITY    = "Indianapolis,US"

GCAL_ICS_URL = "https://calendar.google.com/calendar/ical/YOUR_CALENDAR_ID/basic.ics"

# IP address of your computer running tts_server.py
TTS_SERVER_IP   = "192.168.1.XXX"   # <-- change this to your computer's local IP
TTS_SERVER_PORT = 5001

# Radio stream URLs (MP3, 128kbps recommended)
RADIO_STATION_1_URL  = "http://ice1.somafm.com/groovesalad-128-mp3"
RADIO_STATION_1_NAME = "Groove Salad"
RADIO_STATION_2_URL  = "http://ice1.somafm.com/seventies-128-mp3"
RADIO_STATION_2_NAME = "70s Hits"

# Optional: host alarm.mp3 on the TTS server, or set to None for buzzer tones
ALARM_AUDIO_URL = None   # e.g. "http://192.168.1.XXX:5001/alarm.mp3"

# ─────────────────────────────────────────────
#  GLOBALS
# ─────────────────────────────────────────────
alarm_active  = False
radio_playing = None
snooze_until  = None
weather_text  = ""
calendar_text = ""

# ─────────────────────────────────────────────
#  TIME HELPERS
# ─────────────────────────────────────────────
def sync_time():
    try:
        ntptime.settime()
    except:
        pass

def local_time():
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
        r = urequests.get(url, timeout=10)
        d = ujson.loads(r.text)
        r.close()
        desc  = d["weather"][0]["description"].capitalize()
        temp  = round(d["main"]["temp"])
        feels = round(d["main"]["feels_like"])
        weather_text = (
            "Weather: {}. {} degrees, feels like {}.".format(desc, temp, feels)
        )
    except Exception as e:
        weather_text = "Weather unavailable."
        print("Weather error:", e)

# ─────────────────────────────────────────────
#  GOOGLE CALENDAR
# ─────────────────────────────────────────────
def fetch_calendar():
    global calendar_text
    try:
        r   = urequests.get(GCAL_ICS_URL, timeout=15)
        ics = r.text
        r.close()
        events = parse_ics_today(ics)
        if events:
            calendar_text = "You have {} event{} today. ".format(
                len(events), "s" if len(events) > 1 else "")
            calendar_text += " ".join(events[:5])
        else:
            calendar_text = "No events today."
    except Exception as e:
        calendar_text = "Calendar unavailable."
        print("Calendar error:", e)

def parse_ics_today(ics_text):
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
                try:
                    t_part = dtstart.split("T")[1][:4]
                    h = (int(t_part[:2]) + TZ_OFFSET_HOURS) % 24
                    m = t_part[2:]
                    events.append("{} at {:02d}:{}.".format(summary, h, m))
                except:
                    events.append(summary + ".")
            in_event = False
        elif in_event:
            if line.startswith("SUMMARY:"):
                summary = line[8:]
            elif line.startswith("DTSTART"):
                dtstart = line.split(":")[-1]
    return events

# ─────────────────────────────────────────────
#  TTS  (calls your computer's Flask server)
# ─────────────────────────────────────────────
def tts_speak(text):
    stop_audio()
    chunks = []
    words  = text.split(" ")
    cur    = ""
    for w in words:
        if len(cur) + len(w) + 1 <= 200:
            cur = (cur + " " + w).strip()
        else:
            chunks.append(cur)
            cur = w
    if cur:
        chunks.append(cur)

    for chunk in chunks:
        if not chunk:
            continue
        try:
            safe = chunk.replace(" ", "+").replace("&", "and").replace("'", "")
            url  = "http://{}:{}/speak?text={}".format(
                TTS_SERVER_IP, TTS_SERVER_PORT, safe)
            print("TTS request:", url)
            speaker.playMP3(url)
            utime.sleep(max(2, len(chunk) // 12))
        except Exception as e:
            print("TTS error:", e)

# ─────────────────────────────────────────────
#  AUDIO HELPERS
# ─────────────────────────────────────────────
def stop_audio():
    global radio_playing
    try:
        speaker.playMP3("")
    except:
        pass
    try:
        speaker.stop()
    except:
        pass
    radio_playing = None

def play_buzzer_alarm():
    notes = [659, 659, 0, 659, 0, 523, 659, 0, 784]
    for n in notes:
        if n:
            speaker.tone(n, 200)
        else:
            utime.sleep_ms(200)

# ─────────────────────────────────────────────
#  RADIO
# ─────────────────────────────────────────────
def toggle_radio(station):
    global radio_playing
    if radio_playing == station:
        stop_audio()
        show_status("Radio off")
        return
    stop_audio()
    url  = RADIO_STATION_1_URL  if station == 1 else RADIO_STATION_2_URL
    name = RADIO_STATION_1_NAME if station == 1 else RADIO_STATION_2_NAME
    try:
        speaker.playMP3(url)
        radio_playing = station
        show_status("Radio: " + name)
    except Exception as e:
        show_status("Radio error")
        print("Radio error:", e)

# ─────────────────────────────────────────────
#  ALARM
# ─────────────────────────────────────────────
def check_alarm():
    global alarm_active, snooze_until
    if alarm_active:
        return
    now = utime.time()
    if snooze_until:
        if now < snooze_until:
            return
        snooze_until = None
    lt = local_time()
    if lt[3] == ALARM_HOUR and lt[4] == ALARM_MINUTE:
        trigger_alarm()

def trigger_alarm():
    global alarm_active
    alarm_active = True
    stop_audio()
    draw_alarm_screen()
    if ALARM_AUDIO_URL:
        try:
            speaker.playMP3(ALARM_AUDIO_URL)
        except:
            play_buzzer_alarm()
    else:
        play_buzzer_alarm()

def snooze_alarm():
    global alarm_active, snooze_until
    alarm_active = False
    stop_audio()
    snooze_until = utime.time() + SNOOZE_MINUTES * 60
    show_status("Snoozed {}min".format(SNOOZE_MINUTES))

def dismiss_alarm():
    global alarm_active, snooze_until
    alarm_active = False
    snooze_until = None
    stop_audio()
    morning_briefing()

# ─────────────────────────────────────────────
#  MORNING BRIEFING
# ─────────────────────────────────────────────
def morning_briefing():
    show_status("Fetching briefing...")
    fetch_weather()
    fetch_calendar()
    lt = local_time()
    h  = lt[3]
    if h < 12:   greeting = "Good morning!"
    elif h < 17: greeting = "Good afternoon!"
    else:        greeting = "Good evening!"
    script = "{} Today is {}. The time is {}. {} {}".format(
        greeting, date_str(), time_str(), weather_text, calendar_text)
    print("Briefing text:", script)
    show_status("Speaking...")
    tts_speak(script)
    show_status("Done.")

# ─────────────────────────────────────────────
#  DISPLAY
# ─────────────────────────────────────────────
def draw_alarm_screen():
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.RED)
    lcd.text(lcd.CENTER, 70, "WAKE UP!")
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.WHITE)
    lcd.text(lcd.CENTER, 130, "A = Snooze")
    lcd.text(lcd.CENTER, 160, "B or C = Dismiss")

def draw_clock():
    if alarm_active:
        return
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.WHITE)
    lcd.text(lcd.CENTER, 10, time_str())
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.CYAN)
    lcd.text(lcd.CENTER, 65, date_str())
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(lcd.YELLOW)
    lcd.text(lcd.CENTER, 100, "Alarm {:02d}:{:02d}".format(ALARM_HOUR, ALARM_MINUTE))
    if radio_playing:
        name = RADIO_STATION_1_NAME if radio_playing == 1 else RADIO_STATION_2_NAME
        lcd.setTextColor(lcd.GREEN)
        lcd.text(lcd.CENTER, 125, "Playing: " + name)
    if snooze_until:
        rem = max(0, (snooze_until - utime.time()) // 60)
        lcd.setTextColor(lcd.ORANGE)
        lcd.text(lcd.CENTER, 150, "Snooze: {}min left".format(rem))
    lcd.setTextColor(0x888888)
    lcd.text(8,   220, "Radio1")
    lcd.text(130, 220, "Radio2")
    lcd.text(248, 220, "Brief")

def show_status(msg):
    print(msg)
    if not alarm_active:
        lcd.rect(0, 190, 320, 20, lcd.BLACK, lcd.BLACK)
        lcd.font(lcd.FONT_Default)
        lcd.setTextColor(lcd.WHITE)
        lcd.text(5, 192, msg[:50])

# ─────────────────────────────────────────────
#  BUTTON HANDLERS
# ─────────────────────────────────────────────
def btn_a_pressed():
    if alarm_active:
        snooze_alarm()
    else:
        toggle_radio(1)

def btn_b_pressed():
    if alarm_active:
        dismiss_alarm()
    else:
        toggle_radio(2)

def btn_c_pressed():
    if alarm_active:
        dismiss_alarm()
    else:
        morning_briefing()

btnA.wasPressed(btn_a_pressed)
btnB.wasPressed(btn_b_pressed)
btnC.wasPressed(btn_c_pressed)

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
setScreenColor(0x000000)
sync_time()
show_status("Ready")

last_draw  = 0
last_alarm = 0

while True:
    now = utime.ticks_ms()
    if utime.ticks_diff(now, last_draw) >= 1000:
        draw_clock()
        last_draw = now
    if utime.ticks_diff(now, last_alarm) >= 30000:
        check_alarm()
        last_alarm = now
    utime.sleep_ms(100)
