import urequests
import ujson
import config

_data = {}

def fetch():
    global _data
    try:
        url = ("http://api.openweathermap.org/data/2.5/weather"
               "?q={}&appid={}&units={}".format(
                   config.OWM_CITY, config.OWM_API_KEY, config.OWM_UNITS))
        r = urequests.get(url, timeout=10)
        d = ujson.loads(r.text)
        r.close()
        unit = "F" if config.OWM_UNITS == "imperial" else "C"
        _data = {
            "desc":     d["weather"][0]["description"].capitalize(),
            "condition":d["weather"][0]["main"],
            "temp":     "{}{}".format(round(d["main"]["temp"]), unit),
            "feels":    "{}{}".format(round(d["main"]["feels_like"]), unit),
            "humidity": d["main"]["humidity"],
            "wind":     round(d["wind"]["speed"]),
            "raw_temp": d["main"]["temp"],
        }
        print("[weather] Fetched:", _data["desc"])
    except Exception as e:
        print("[weather] Error:", e)

def full_data():
    return _data

def summary_short():
    if not _data:
        return "No weather data"
    return "{} | {} feels {}".format(
        _data.get("desc",""),
        _data.get("temp",""),
        _data.get("feels",""))

def tts_string():
    if not _data:
        return "Weather data is unavailable."
    unit_word = "Fahrenheit" if config.OWM_UNITS == "imperial" else "Celsius"
    return ("{desc}. {temp} degrees {unit_word}, "
            "feels like {feels}. Humidity {humidity} percent.").format(
        unit_word=unit_word, **_data)

def current_condition():
    return _data.get("condition", "Clear")

def is_hot():
    t = _data.get("raw_temp", 70)
    return t > (90 if config.OWM_UNITS == "imperial" else 32)

def is_cold():
    t = _data.get("raw_temp", 70)
    return t < (32 if config.OWM_UNITS == "imperial" else 0)
