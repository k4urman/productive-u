import utime
import clock
import config
import pomodoro
import ticker
import tasks
import macros
import mqtt_ha

try:
    from m5stack import lcd, axp
    from machine import ADC, Pin
    _HW = True
except Exception:
    _HW = False

try:
    _adc = ADC(Pin(36))
    _adc.atten(ADC.ATTN_11DB)
    _ADC_OK = True
except Exception:
    _ADC_OK = False

_last_brightness = -1
_overlay_msg      = ""
_overlay_until    = 0


def splash_screen():
    if not _HW:
        return
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.WHITE)
    lcd.text(lcd.CENTER, 55, "Productive")
    lcd.setTextColor(lcd.CYAN)
    lcd.text(lcd.CENTER, 105, "U")
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(0x888888)
    lcd.text(lcd.CENTER, 165, "M5Stack Fire")
    utime.sleep(2)


def tick():
    _update_brightness()
    if pomodoro.is_active():
        _draw_pomodoro()
    else:
        _draw_ticker()
    _draw_overlay()


def update_all():
    tick()


def show_overlay(msg, duration_ms=2000):
    global _overlay_msg, _overlay_until
    _overlay_msg   = str(msg)[:40]
    _overlay_until = utime.ticks_ms() + duration_ms


def show_status(msg):
    show_overlay(msg, 1500)


def _update_brightness():
    global _last_brightness
    if not _HW:
        return
    raw = _adc.read() if _ADC_OK else 2000
    is_night = raw < config.AMBIENT_NIGHT_THRESHOLD
    target   = (config.SCREEN_BRIGHTNESS_NIGHT if is_night
                else config.SCREEN_BRIGHTNESS_DAY)
    if target != _last_brightness:
        try:
            axp.setLcdBrightness(target)
        except Exception:
            pass
        _last_brightness = target


def _draw_pomodoro():
    if not _HW:
        return

    remaining = pomodoro.remaining()
    m, s      = divmod(remaining, 60)
    phase     = pomodoro.state()

    bg = config.COLOR_WORK if phase == pomodoro.STATE_WORK else config.COLOR_BREAK
    try:
        lcd.fill(0, 0, 320, 240, bg)
    except Exception:
        lcd.clear()

    lcd.font(lcd.FONT_DejaVu40)
    lcd.setTextColor(lcd.WHITE, bg)
    lcd.text(lcd.CENTER, 35, "{:02d}:{:02d}".format(m, s))

    lcd.font(lcd.FONT_DejaVu24)
    label = pomodoro.phase_label()
    if not pomodoro.is_running():
        label += "  ||"
    lcd.text(lcd.CENTER, 95, label)

    lcd.font(lcd.FONT_DejaVu18)
    task = tasks.current_label()
    if task:
        lcd.text(lcd.CENTER, 130, task)

    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(0xEEEEEE, bg)
    lcd.text(5, 200, "A:Layer")
    lcd.text(110, 200, "B:Pause")
    lcd.text(220, 200, "C:Skip")

    if pomodoro.completed_work() > 0:
        lcd.text(lcd.CENTER, 175, "Done: {}".format(pomodoro.completed_work()))


def _draw_ticker():
    if not _HW:
        return

    lcd.clear(config.COLOR_IDLE)

    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.CYAN, config.COLOR_IDLE)
    lcd.text(lcd.CENTER, 8, ticker.subtitle())

    lcd.font(lcd.FONT_DejaVu24)
    lcd.setTextColor(lcd.WHITE, config.COLOR_IDLE)
    line = ticker.line()
    if len(line) > 28:
        lcd.text(5, 55, line[:28])
        lcd.text(5, 85, line[28:56])
    else:
        lcd.text(lcd.CENTER, 70, line)

    _draw_mqtt_strip(120)

    task = tasks.current_label()
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.YELLOW, config.COLOR_IDLE)
    if task:
        lcd.text(lcd.CENTER, 150, "Tracking: " + task)
    else:
        lcd.text(lcd.CENTER, 150, "Flip to pick task")

    layer = macros.layer_name()
    lcd.font(lcd.FONT_Default)
    lcd.setTextColor(0x888888, config.COLOR_IDLE)
    lcd.text(5,   200, "A:" + layer[:8])
    lcd.text(110, 200, "B:Act")
    lcd.text(220, 200, "C:Act")


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
        parts.append("DOORBELL")
    if data.get("next_event"):
        parts.append(data["next_event"][:22])
    if parts:
        lcd.font(lcd.FONT_Default)
        lcd.setTextColor(lcd.YELLOW, config.COLOR_IDLE)
        lcd.text(lcd.CENTER, y, "  ".join(parts)[:42])


def _draw_overlay():
    global _overlay_msg
    if not _HW or not _overlay_msg:
        return
    if utime.ticks_diff(_overlay_until, utime.ticks_ms()) <= 0:
        _overlay_msg = ""
        return
    lcd.rect(0, 175, 320, 28, lcd.BLACK, lcd.BLACK)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.setTextColor(lcd.WHITE, lcd.BLACK)
    lcd.text(lcd.CENTER, 180, _overlay_msg)
