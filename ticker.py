import utime
import clock
import config
import weather
import calendar_ics

_sources = ["calendar", "weather", "time"]
_idx     = 0
_last_rotate = 0


def init():
    global _last_rotate
    _last_rotate = utime.time()
    print("[ticker] sources:", _sources)


def current_source():
    return _sources[_idx % len(_sources)]


def next_source():
    global _idx, _last_rotate
    _idx = (_idx + 1) % len(_sources)
    _last_rotate = utime.time()
    print("[ticker] →", current_source())


def tick_auto_rotate():
    if config.TICKER_ROTATE_SECONDS <= 0:
        return
    if utime.time() - _last_rotate >= config.TICKER_ROTATE_SECONDS:
        next_source()


def refresh():
    global _last_rotate
    src = current_source()
    if src == "weather":
        weather.fetch()
    elif src == "calendar":
        calendar_ics.fetch()
    _last_rotate = utime.time()


def line():
    src = current_source()
    if src == "calendar":
        ev = calendar_ics.next_event_str()
        return ("NEXT  " + ev) if ev else "NEXT  No events today"
    if src == "weather":
        return "WX    " + weather.summary_short()
    return "TIME  " + clock.time_hhmm() + "  " + clock.date_str()


def subtitle():
    src = current_source()
    if src == "calendar":
        return "Google Calendar"
    if src == "weather":
        return config.OWM_CITY
    return "Local clock"
