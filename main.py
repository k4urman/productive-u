import utime
import gc

from m5stack import *
from m5ui import *
from uiflow import *
import config

import clock
import display
import leds
import pomodoro
import tasks
import macros
import agent
import ticker
import weather
import calendar_ics
import mqtt_ha
import imu
import voice_memo

try:
    from m5stack import btnPower
    _HAS_POWER = True
except Exception:
    _HAS_POWER = False

_power_down_ms = 0
_power_recording = False


def boot():
    setScreenColor(0x000000)
    lcd.clear()
    display.splash_screen()
    clock.init()
    leds.init()
    imu.init()
    pomodoro.init()
    tasks.init()
    macros.init()
    ticker.init()
    weather.fetch()
    calendar_ics.fetch()
    mqtt_ha.connect()
    display.update_all()
    print("[main] Productive-U ready")


def on_a():
    if voice_memo.is_recording():
        return
    macros.cycle_layer()


def on_b():
    if voice_memo.is_recording():
        return
    if pomodoro.is_active():
        pomodoro.toggle_pause()
        display.show_overlay("Pause" if not pomodoro.is_running() else "Resume", 800)
    else:
        macros.fire_b()


def on_c():
    if voice_memo.is_recording():
        return
    if pomodoro.is_active():
        pomodoro.skip_phase()
        display.show_overlay("Skip", 800)
    else:
        macros.fire_c()


btnA.wasPressed(on_a)
btnB.wasPressed(on_b)
btnC.wasPressed(on_c)


def _tick_power_button():
    global _power_down_ms, _power_recording

    if not _HAS_POWER:
        return

    try:
        pressed = btnPower.isPressed()
    except Exception:
        return

    now = utime.ticks_ms()

    if pressed:
        if _power_down_ms == 0:
            _power_down_ms = now
        elif (not _power_recording and
              utime.ticks_diff(now, _power_down_ms) >= config.MEMO_POWER_HOLD_MS):
            if voice_memo.start():
                _power_recording = True
                display.show_overlay("REC...", 60000)
        if _power_recording:
            voice_memo.tick_sample()
    else:
        if _power_recording:
            path = voice_memo.stop()
            _power_recording = False
            if path:
                display.show_overlay("Saved memo", 2000)
            else:
                display.show_overlay("Memo failed", 2000)
        _power_down_ms = 0


TICK_DISPLAY  = 250
TICK_POMODORO = 1000
TICK_AGENT    = 3000
TICK_WEATHER  = 600000
TICK_CALENDAR = 300000
TICK_IMU      = 200
TICK_MQTT     = 500
TICK_LED      = 400
TICK_TICKER   = 1000
TICK_GC       = 30000

last = {k: 0 for k in (
    "display", "pomodoro", "agent", "weather", "calendar",
    "imu", "mqtt", "led", "ticker", "gc")}

boot()

while True:
    now = utime.ticks_ms()

    _tick_power_button()

    if utime.ticks_diff(now, last["imu"]) >= TICK_IMU:
        imu.tick()
        last["imu"] = now

    if utime.ticks_diff(now, last["pomodoro"]) >= TICK_POMODORO:
        pomodoro.tick()
        last["pomodoro"] = now

    if utime.ticks_diff(now, last["display"]) >= TICK_DISPLAY:
        display.tick()
        last["display"] = now

    if utime.ticks_diff(now, last["ticker"]) >= TICK_TICKER:
        ticker.tick_auto_rotate()
        last["ticker"] = now

    if utime.ticks_diff(now, last["agent"]) >= TICK_AGENT:
        agent.fetch_status()
        last["agent"] = now

    if utime.ticks_diff(now, last["weather"]) >= TICK_WEATHER:
        weather.fetch()
        last["weather"] = now

    if utime.ticks_diff(now, last["calendar"]) >= TICK_CALENDAR:
        calendar_ics.fetch()
        last["calendar"] = now

    if utime.ticks_diff(now, last["mqtt"]) >= TICK_MQTT:
        mqtt_ha.tick()
        last["mqtt"] = now

    if utime.ticks_diff(now, last["led"]) >= TICK_LED:
        leds.tick()
        last["led"] = now

    if utime.ticks_diff(now, last["gc"]) >= TICK_GC:
        gc.collect()
        last["gc"] = now

    utime.sleep_ms(30)
