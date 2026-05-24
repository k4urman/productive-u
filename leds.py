import utime
import math
import config
import agent

try:
    from machine import Pin
    import neopixel
    _LED_PIN   = 15
    _LED_COUNT = 10
    _np = neopixel.NeoPixel(Pin(_LED_PIN), _LED_COUNT)
    _HW = True
except Exception as e:
    print("[leds] Hardware not available:", e)
    _HW = False
    _np = None

_mode          = "off"
_pulse_phase   = 0.0
_pulse_ticks   = 0
_render_pulses = 0


def init():
    off()
    print("[leds] init OK")


def tick():
    global _pulse_phase, _pulse_ticks, _render_pulses, _mode

    status = agent.get_status()

    if status.get("mic_hot"):
        _mode = "mic"
        _apply_color(config.LED_COLOR_MIC_HOT)
        return

    if status.get("render_done") and _render_pulses < 6:
        _mode = "render"
        _pulse_ticks += 1
        if _pulse_ticks >= 8:
            _pulse_ticks = 0
            _pulse_phase += 1.0
            _render_pulses += 1
        factor = (math.sin(_pulse_phase) + 1) / 2
        c = config.LED_COLOR_RENDER_DONE
        _apply_color((int(c[0] * factor), int(c[1] * factor), int(c[2] * factor)))
        if _render_pulses >= 6:
            agent.ack_render_done()
            _render_pulses = 0
            off()
        return

    if _mode != "off":
        off()


def off():
    global _mode
    _mode = "off"
    _set_all(0, 0, 0)


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
