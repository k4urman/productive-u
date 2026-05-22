import utime
import gc

# ── Core init ────────────────────────────────────────────
from m5stack import *
from m5ui   import *
from uiflow import *
import config

# ── Module imports ────────────────────────────────────────
import clock
import display
import leds
import alarm
import radio
import weather
import calendar_ics
import tts
import mqtt_ha
import imu
import chime
import modes

# ─────────────────────────────────────────────────────────
#  BOOT SEQUENCE
# ─────────────────────────────────────────────────────────
def boot():
    setScreenColor(0x000000)
    lcd.clear()
    display.splash_screen()          # animated boot logo
    clock.init()                     # NTP sync + DST check
    leds.init()                      # LED bars off → dim white
    imu.init()                       # accelerometer
    weather.fetch()                  # first weather pull
    calendar_ics.fetch()             # first calendar pull
    mqtt_ha.connect()                # HA / MQTT (non-blocking)
    chime.init()                     # schedule hourly chimes
    modes.set_mode(modes.MODE_CLOCK) # start in clock mode
    display.update_all()
    leds.weather_glow(weather.current_condition())

# ─────────────────────────────────────────────────────────
#  BUTTON HANDLERS  (context-aware, set once here)
# ─────────────────────────────────────────────────────────
def on_a():
    if alarm.is_ringing():
        alarm.snooze()
    elif modes.current() == modes.MODE_TIMER:
        modes.timer_start_stop()
    elif modes.current() == modes.MODE_KITCHEN:
        modes.kitchen_start_stop()
    else:
        radio.toggle(1)

def on_b():
    if alarm.is_ringing():
        alarm.dismiss()
    elif modes.current() == modes.MODE_TIMER:
        modes.timer_reset()
    elif modes.current() == modes.MODE_KITCHEN:
        modes.kitchen_reset()
    else:
        radio.toggle(2)

def on_c():
    if alarm.is_ringing():
        alarm.dismiss()
    else:
        tts.morning_briefing()

btnA.wasPressed(on_a)
btnB.wasPressed(on_b)
btnC.wasPressed(on_c)

# ─────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────
# Tick intervals (ms)
TICK_DISPLAY  =  250   # screen redraw
TICK_ALARM    = 5000   # alarm check
TICK_CHIME    = 1000   # chime engine
TICK_WEATHER  = 600000 # 10 min
TICK_CALENDAR = 300000 # 5 min
TICK_IMU      =  200   # accelerometer / mode rotate
TICK_MQTT     =  500   # MQTT pump
TICK_LED      = 1000   # LED update
TICK_GC       = 30000  # garbage collect

last = {k: 0 for k in
        ("display","alarm","chime","weather","calendar","imu","mqtt","led","gc")}

boot()

while True:
    now = utime.ticks_ms()

    if utime.ticks_diff(now, last["imu"]) >= TICK_IMU:
        imu.tick()          # screen-flip + rotation detect → mode change
        last["imu"] = now

    if utime.ticks_diff(now, last["display"]) >= TICK_DISPLAY:
        display.tick()
        last["display"] = now

    if utime.ticks_diff(now, last["alarm"]) >= TICK_ALARM:
        alarm.tick()
        last["alarm"] = now

    if utime.ticks_diff(now, last["chime"]) >= TICK_CHIME:
        chime.tick()
        last["chime"] = now

    if utime.ticks_diff(now, last["weather"]) >= TICK_WEATHER:
        weather.fetch()
        leds.weather_glow(weather.current_condition())
        last["weather"] = now

    if utime.ticks_diff(now, last["calendar"]) >= TICK_CALENDAR:
        calendar_ics.fetch()
        last["calendar"] = now

    if utime.ticks_diff(now, last["mqtt"]) >= TICK_MQTT:
        mqtt_ha.tick()
        last["mqtt"] = now

    if utime.ticks_diff(now, last["led"]) >= TICK_LED:
        leds.tick()         # handles breathe / sunrise animation
        last["led"] = now

    if utime.ticks_diff(now, last["gc"]) >= TICK_GC:
        gc.collect()
        last["gc"] = now

    utime.sleep_ms(50)
