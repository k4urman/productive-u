import config

try:
    from m5stack import speaker
    _HW = True
except Exception:
    _HW = False

_playing = None   # None | 1 | 2

def toggle(station):
    global _playing
    if _playing == station:
        stop()
        return
    stop()
    url  = config.RADIO_STATION_1_URL  if station == 1 else config.RADIO_STATION_2_URL
    name = config.RADIO_STATION_1_NAME if station == 1 else config.RADIO_STATION_2_NAME
    try:
        if _HW:
            speaker.playMP3(url)
        _playing = station
        print("[radio] Playing:", name)
    except Exception as e:
        print("[radio] Error:", e)

def stop():
    global _playing
    if _HW:
        try:
            speaker.playMP3("")
        except Exception:
            pass
        try:
            speaker.stop()
        except Exception:
            pass
    _playing = None

def is_playing():
    return _playing is not None

def current_name():
    if _playing == 1:
        return config.RADIO_STATION_1_NAME
    if _playing == 2:
        return config.RADIO_STATION_2_NAME
    return ""
