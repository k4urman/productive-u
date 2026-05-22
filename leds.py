import utime
import math
import config

try:
    from m5stack import axp
    from machine import Pin
    import neopixel
    _LED_PIN  = 15    # M5Stack Fire SK6812 data pin
    _LED_COUNT = 10
    _np = neopixel.NeoPixel(Pin(_LED_PIN), _LED_COUNT)
    _HW = True
except Exception as e:
    print("[leds] Hardware not available:", e)
    _HW = False
    _np = None

# ── State ────────────────────────────────────────────────
_mode          = "off"       # "off" | "glow" | "breathe" | "sunrise"
_base_color    = (0, 0, 0)
_sunrise_start = 0           # epoch when sunrise animation started
_sunrise_dur   = 0           # total duration in seconds
_breathe_phase = 0.0
_last_tick     = 0

def init():
    _set_all(0, 0, 0)
    print("[leds] init OK")

# ─────────────────────────────────────────────────────────
#  PUBLIC API
# ─────────────────────────────────────────────────────────
def weather_glow(condition):
    """Set LED color based on weather condition string."""
    global _mode, _base_color
    c = condition.lower()
    if   "thunder" in c or "storm"  in c: col = config.LED_COLOR_STORM
    elif "snow"    in c or "sleet"  in c: col = config.LED_COLOR_SNOW
    elif "rain"    in c or "drizzle"in c: col = config.LED_COLOR_RAIN
    elif "cloud"   in c or "overcast"in c:col = config.LED_COLOR_CLOUDY
    elif "clear"   in c or "sun"    in c: col = config.LED_COLOR_CLEAR
    else:                                  col = config.LED_COLOR_CLEAR
    _base_color = col
    _mode = "breathe" if config.LED_BREATHE_ENABLED else "glow"
    _apply_color(_base_color)

def hot_alert():
    global _base_color, _mode
    _base_color = config.LED_COLOR_HOT
    _mode = "breathe"

def cold_alert():
    global _base_color, _mode
    _base_color = config.LED_COLOR_COLD
    _mode = "breathe"

def start_sunrise(duration_seconds):
    """Begin sunrise animation over `duration_seconds`."""
    global _mode, _sunrise_start, _sunrise_dur
    _mode = "sunrise"
    _sunrise_start = utime.time()
    _sunrise_dur   = duration_seconds
    print("[leds] Sunrise started, duration={}s".format(duration_seconds))

def stop_sunrise():
    global _mode
    _mode = "off"
    _set_all(0, 0, 0)

def alarm_flash():
    """Brief attention flash when alarm rings."""
    for _ in range(3):
        _set_all(255, 80, 0)
        utime.sleep_ms(200)
        _set_all(0, 0, 0)
        utime.sleep_ms(150)

def off():
    global _mode
    _mode = "off"
    _set_all(0, 0, 0)

# ─────────────────────────────────────────────────────────
#  TICK  (called from main loop every ~1 s)
# ─────────────────────────────────────────────────────────
def tick():
    global _breathe_phase

    if _mode == "off":
        return

    elif _mode == "glow":
        _apply_color(_base_color)

    elif _mode == "breathe":
        _breathe_phase += 0.08   # ~12 s full cycle at 1 Hz tick
        factor = (math.sin(_breathe_phase) + 1) / 2   # 0.0 → 1.0
        # Scale between 30% and 100% of base
        scale  = 0.30 + 0.70 * factor
        r = int(_base_color[0] * scale)
        g = int(_base_color[1] * scale)
        b = int(_base_color[2] * scale)
        _apply_color((r, g, b))

    elif _mode == "sunrise":
        elapsed  = utime.time() - _sunrise_start
        progress = min(1.0, elapsed / max(1, _sunrise_dur))
        r = int(_lerp(config.LED_SUNRISE_START[0], config.LED_SUNRISE_END[0], progress))
        g = int(_lerp(config.LED_SUNRISE_START[1], config.LED_SUNRISE_END[1], progress))
        b = int(_lerp(config.LED_SUNRISE_START[2], config.LED_SUNRISE_END[2], progress))
        _apply_color((r, g, b))
        if progress >= 1.0:
            # Hold at full sunrise color — alarm will dismiss
            pass

# ─────────────────────────────────────────────────────────
#  INTERNAL HELPERS
# ─────────────────────────────────────────────────────────
def _lerp(a, b, t):
    return a + (b - a) * t

def _scale(color, brightness_0_255):
    f = brightness_0_255 / 255.0
    return (int(color[0]*f), int(color[1]*f), int(color[2]*f))

def _apply_color(color):
    cap = config.LED_BRIGHTNESS_MAX / 255.0
    r   = int(color[0] * cap)
    g   = int(color[1] * cap)
    b   = int(color[2] * cap)
    _set_all(r, g, b)

def _set_all(r, g, b):
    if not _HW or _np is None:
        return
    for i in range(_LED_COUNT):
        _np[i] = (r, g, b)
    _np.write()
