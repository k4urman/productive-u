import utime
import config
import clock
import leds
import display
import tts
import chime

# ── State ────────────────────────────────────────────────
_ringing      = False
_snooze_until = None   # epoch
_sunrise_fired= False
_preview_fired= False

# ─────────────────────────────────────────────────────────
#  TICK  (called every 5 s from main loop)
# ─────────────────────────────────────────────────────────
def tick():
    global _ringing, _snooze_until, _sunrise_fired, _preview_fired

    if not config.ALARM_ENABLED:
        return
    if _ringing:
        return

    now_epoch = clock.epoch()
    lt        = clock.local_time()
    now_hm    = lt[3] * 60 + lt[4]        # minutes since midnight
    alarm_hm  = config.ALARM_HOUR * 60 + config.ALARM_MINUTE

    # Snooze active?
    if _snooze_until:
        if now_epoch < _snooze_until:
            return
        _snooze_until = None

    # Sunrise pre-alarm
    sunrise_hm = alarm_hm - config.SUNRISE_PRE_ALARM_MINUTES
    if not _sunrise_fired and now_hm == sunrise_hm:
        _sunrise_fired = True
        dur = config.SUNRISE_PRE_ALARM_MINUTES * 60
        leds.start_sunrise(dur)
        print("[alarm] Sunrise LED started")

    # Soft preview chime 2 min before
    if not _preview_fired and now_hm == alarm_hm - 2:
        _preview_fired = True
        chime.play_preview()

    # Fire alarm
    if now_hm == alarm_hm:
        _trigger()

    # Reset daily flags after alarm window
    if now_hm > alarm_hm + 2:
        _sunrise_fired = False
        _preview_fired = False

def _trigger():
    global _ringing
    _ringing = True
    display.draw_alarm_ringing()
    leds.alarm_flash()
    _play_alarm_sound()
    print("[alarm] RINGING")

def _play_alarm_sound():
    if config.ALARM_AUDIO_URL:
        try:
            from m5stack import speaker
            speaker.playMP3(config.ALARM_AUDIO_URL)
            return
        except Exception as e:
            print("[alarm] MP3 error:", e)
    # Buzzer fallback
    _buzzer_melody()

def _buzzer_melody():
    from m5stack import speaker
    notes = [659, 0, 659, 0, 523, 659, 0, 784, 0, 392]
    for n in notes:
        if n:
            speaker.tone(n, 180)
        utime.sleep_ms(220)

# ─────────────────────────────────────────────────────────
#  SNOOZE / DISMISS
# ─────────────────────────────────────────────────────────
def snooze():
    global _ringing, _snooze_until
    if not _ringing:
        return
    _ringing = False
    _stop_audio()
    _snooze_until = clock.epoch() + config.SNOOZE_MINUTES * 60
    display.show_status("Snoozed {}min".format(config.SNOOZE_MINUTES))
    print("[alarm] Snoozed")

def dismiss():
    global _ringing, _snooze_until
    _ringing = False
    _snooze_until = None
    _stop_audio()
    leds.stop_sunrise()
    print("[alarm] Dismissed → briefing")
    tts.morning_briefing()

def is_ringing():
    return _ringing

def _stop_audio():
    try:
        from m5stack import speaker
        speaker.stop()
    except Exception:
        pass
