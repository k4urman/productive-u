import utime
import math
import clock
import config
import weather
import mqtt_ha
import modes
import radio

try:
    from m5stack import lcd, axp
    from machine  import ADC, Pin
    _HW = True
except Exception:
    _HW = False

# ── Ambient light sensor ─────────────────────────────────
try:
    _adc = ADC(Pin(36))          # VP pin, M5Stack Fire
    _adc.atten(ADC.ATTN_11DB)
    _ADC_OK = True
except Exception:
    _ADC_OK = False

# ── GIF state ────────────────────────────────────────────
_gif_frames  = []
_gif_idx     = 0
_gif_loaded  = False

# ── Circadian state ──────────────────────────────────────
_last_brightness = -1

# ─────────────────────────────────────────────────────────
#  BOOT
# ─────────────────────────────────────────────────────────
def splash_screen():
    if not _HW:
        return
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.WHITE)
    lcd.text(lcd.CENTER, 60, "ULTIMATE")
    lcd.setTextColor(lcd.CYAN)
    lcd.text(lcd.CENTER, 110, "CLOCK")
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(0x888888)
    lcd.text(lcd.CENTER, 165, "v3.0  — M5Stack Fire")
    utime.sleep(2)
    _load_gif()

def _load_gif():
    global _gif_frames, _gif_loaded
    if not config.GIF_BACKGROUND:
        return
    try:
        import os
        frame_dir = config.GIF_BACKGROUND
        files = [f for f in os.listdir(frame_dir) if f.endswith(".rgb")]
        files.sort()
        _gif_frames = [frame_dir + "/" + f for f in files]
        _gif_loaded = len(_gif_frames) > 0
        print("[display] GIF loaded: {} frames".format(len(_gif_frames)))
    except Exception as e:
        print("[display] GIF load failed:", e)
        _gif_loaded = False

# ─────────────────────────────────────────────────────────
#  AMBIENT DIMMING + CIRCADIAN
# ─────────────────────────────────────────────────────────
def _update_brightness():
    global _last_brightness
    if not _HW:
        return
    raw = _adc.read() if _ADC_OK else 2000
    is_night = raw < config.AMBIENT_NIGHT_THRESHOLD
    target   = config.SCREEN_BRIGHTNESS_NIGHT if is_night else config.SCREEN_BRIGHTNESS_DAY
    if target != _last_brightness:
        try:
            axp.setLcdBrightness(target)
        except Exception:
            pass
        _last_brightness = target

def _circadian_tint():
    """Return (r_add, g_add, b_add) warm offset for night hours."""
    if not config.CIRCADIAN_ENABLED:
        return (0, 0, 0)
    h = clock.hour()
    # Warm at 20:00-06:00, neutral at 10:00-17:00, smooth ramp between
    if 10 <= h <= 17:
        return (0, 0, 0)
    if h >= 20 or h <= 6:
        return (40, 15, -20)   # warm orange tint
    # Ramp zones
    if 17 < h < 20:
        t = (h - 17) / 3.0
        return (int(40*t), int(15*t), int(-20*t))
    if 6 < h < 10:
        t = 1.0 - (h - 6) / 4.0
        return (int(40*t), int(15*t), int(-20*t))
    return (0, 0, 0)

# ─────────────────────────────────────────────────────────
#  TICK — called every 250 ms from main loop
# ─────────────────────────────────────────────────────────
def tick():
    _update_brightness()
    mode = modes.current()
    if   mode == modes.MODE_CLOCK:   _draw_clock()
    elif mode == modes.MODE_TIMER:   _draw_timer()
    elif mode == modes.MODE_KITCHEN: _draw_kitchen()
    elif mode == modes.MODE_WEATHER: _draw_weather_full()

def update_all():
    tick()

# ─────────────────────────────────────────────────────────
#  GIF BACKGROUND
# ─────────────────────────────────────────────────────────
def _draw_gif_frame():
    global _gif_idx
    if not _gif_loaded or not _HW:
        return
    try:
        path = _gif_frames[_gif_idx]
        lcd.image(0, 0, path)   # M5GFX can blit raw RGB565 image file
        _gif_idx = (_gif_idx + 1) % len(_gif_frames)
    except Exception as e:
        pass   # silently skip bad frames

# ─────────────────────────────────────────────────────────
#  CLOCK FACE
# ─────────────────────────────────────────────────────────
def _draw_clock():
    if not _HW:
        return
    lcd.clear()
    _draw_gif_frame()

    tint = _circadian_tint()
    white = _tinted(0xFF, 0xFF, 0xFF, tint)
    cyan  = _tinted(0x00, 0xFF, 0xFF, tint)
    grey  = 0x888888

    # Large anti-aliased time (DejaVu40 is the smoothest built-in)
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(white, lcd.BLACK)
    lcd.text(lcd.CENTER, 8, clock.time_hhmm())

    # Seconds — smaller, right-aligned feel
    lcd.font(lcd.FONT_DejaVu24)
    lcd.setTextColor(cyan, lcd.BLACK)
    lcd.text(lcd.CENTER, 62, ":{:02d}".format(clock.second()))

    # Date
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(cyan, lcd.BLACK)
    lcd.text(lcd.CENTER, 95, clock.date_str())

    # DST badge
    if clock.is_dst():
        lcd.font(lcd.FONT_Default)
        lcd.setTextColor(lcd.YELLOW, lcd.BLACK)
        lcd.text(5, 95, "DST")

    # Weather strip
    w = weather.summary_short()
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(white, lcd.BLACK)
    lcd.text(lcd.CENTER, 120, w)

    # MQTT overlay
    _draw_mqtt_strip(140)

    # Radio indicator
    if radio.is_playing():
        lcd.setTextColor(lcd.GREEN, lcd.BLACK)
        lcd.text(lcd.CENTER, 165, "♫ " + radio.current_name())

    # Button hints
    lcd.setTextColor(grey, lcd.BLACK)
    lcd.text(8,   220, "Radio1")
    lcd.text(127, 220, "Radio2")
    lcd.text(248, 220, "Brief")

# ─────────────────────────────────────────────────────────
#  COUNTDOWN TIMER FACE
# ─────────────────────────────────────────────────────────
def _draw_timer():
    if not _HW:
        return
    lcd.clear()
    remaining = modes.timer_remaining()
    m, s = divmod(remaining, 60)
    lcd.font(lcd.FONT_DejaVu40)
    color = lcd.RED if remaining <= 10 else lcd.WHITE
    lcd.setTextColor(color, lcd.BLACK)
    lcd.text(lcd.CENTER, 60, "{:02d}:{:02d}".format(m, s))
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.CYAN, lcd.BLACK)
    lcd.text(lcd.CENTER, 120, "COUNTDOWN")
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(0x888888, lcd.BLACK)
    lcd.text(8,   220, "Start/Stop")
    lcd.text(200, 220, "Reset")

# ─────────────────────────────────────────────────────────
#  KITCHEN ALARM FACE
# ─────────────────────────────────────────────────────────
def _draw_kitchen():
    if not _HW:
        return
    lcd.clear()
    elapsed = modes.kitchen_elapsed()
    target  = modes.kitchen_target()
    m, s    = divmod(elapsed, 60)
    tm, ts  = divmod(target, 60)
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.YELLOW, lcd.BLACK)
    lcd.text(lcd.CENTER, 40, "{:02d}:{:02d}".format(m, s))
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(0x888888, lcd.BLACK)
    lcd.text(lcd.CENTER, 100, "Target {:02d}:{:02d}".format(tm, ts))
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(0x888888, lcd.BLACK)
    lcd.text(8,   220, "Start/Stop")
    lcd.text(200, 220, "Reset")

# ─────────────────────────────────────────────────────────
#  WEATHER DASHBOARD FACE
# ─────────────────────────────────────────────────────────
def _draw_weather_full():
    if not _HW:
        return
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu24)
    lcd.setTextColor(lcd.CYAN, lcd.BLACK)
    lcd.text(lcd.CENTER, 5, "WEATHER")

    data = weather.full_data()
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.WHITE, lcd.BLACK)
    lcd.text(10, 40,  data.get("desc",""))
    lcd.text(10, 65,  "Temp:     {}°".format(data.get("temp","-")))
    lcd.text(10, 85,  "Feels:    {}°".format(data.get("feels","-")))
    lcd.text(10, 105, "Humidity: {}%".format(data.get("humidity","-")))
    lcd.text(10, 125, "Wind:     {} mph".format(data.get("wind","-")))

    _draw_mqtt_strip(160)

    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(0x888888, lcd.BLACK)
    lcd.text(lcd.CENTER, 220, "Rotate to switch modes")

# ─────────────────────────────────────────────────────────
#  MQTT OVERLAY STRIP
# ─────────────────────────────────────────────────────────
def _draw_mqtt_strip(y):
    if not _HW:
        return
    data = mqtt_ha.get_data()
    parts = []
    if data.get("indoor_temp"):
        parts.append("In: {}°".format(data["indoor_temp"]))
    if data.get("aqi"):
        parts.append("AQI: {}".format(data["aqi"]))
    if data.get("doorbell"):
        parts.append("** DOORBELL **")
    if data.get("next_event"):
        parts.append(data["next_event"][:25])
    if parts:
        lcd.font(lcd.FONT_Default)
        lcd.setTextColor(lcd.YELLOW, lcd.BLACK)
        lcd.text(lcd.CENTER, y, "  ".join(parts))

# ─────────────────────────────────────────────────────────
#  ALARM SCREEN
# ─────────────────────────────────────────────────────────
def draw_alarm_ringing():
    if not _HW:
        return
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.RED, lcd.BLACK)
    lcd.text(lcd.CENTER, 60, "WAKE UP!")
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.WHITE, lcd.BLACK)
    lcd.text(lcd.CENTER, 125, clock.time_hhmm())
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(0x888888, lcd.BLACK)
    lcd.text(8,   220, "Snooze")
    lcd.text(110, 220, "Dismiss")

# ─────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────
def _tinted(r, g, b, tint):
    r2 = max(0, min(255, r + tint[0]))
    g2 = max(0, min(255, g + tint[1]))
    b2 = max(0, min(255, b + tint[2]))
    return (r2 << 16) | (g2 << 8) | b2

def show_status(msg):
    if not _HW:
        return
    print("[status]", msg)
    lcd.rect(0, 190, 320, 18, lcd.BLACK, lcd.BLACK)
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(lcd.WHITE, lcd.BLACK)
    lcd.text(5, 192, str(msg)[:52])
