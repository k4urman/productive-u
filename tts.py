import utime
import config
import clock
import weather
import calendar_ics
import display
import radio

try:
    from m5stack import speaker
    _HW = True
except Exception:
    _HW = False

def _speak(text):
    """Send text to TTS server in <=200-char chunks and play each as MP3."""
    radio.stop()
    words, chunks, cur = text.split(" "), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= 200:
            cur = (cur + " " + w).strip()
        else:
            chunks.append(cur); cur = w
    if cur:
        chunks.append(cur)

    for chunk in chunks:
        if not chunk:
            continue
        safe = chunk.replace(" ", "+").replace("&", "and").replace("'", "")
        url  = "http://{}:{}/speak?text={}".format(
            config.TTS_SERVER_IP, config.TTS_SERVER_PORT, safe)
        print("[tts]", url)
        try:
            if _HW:
                speaker.playMP3(url)
            utime.sleep(max(2, len(chunk) // 12))
        except Exception as e:
            print("[tts] Error:", e)

def morning_briefing():
    display.show_status("Building briefing...")
    h = clock.hour()
    if   h < 12: greeting = "Good morning!"
    elif h < 17: greeting = "Good afternoon!"
    else:        greeting = "Good evening!"

    script = (
        "{greeting} Today is {date}. The time is {time}. "
        "{weather} "
        "{calendar}"
    ).format(
        greeting = greeting,
        date     = clock.date_str(),
        time     = clock.time_hhmm(),
        weather  = weather.tts_string(),
        calendar = calendar_ics.tts_string(),
    )
    print("[tts] Briefing:", script)
    display.show_status("Speaking briefing...")
    _speak(script)
    display.show_status("Briefing done.")

def speak(text):
    _speak(text)
