import utime
import config
import clock

try:
    from m5stack import speaker
    _HW = True
except Exception:
    _HW = False

# ── Note frequencies (Hz) ────────────────────────────────
NOTE = {
    "C4":262,"D4":294,"E4":330,"F4":349,"G4":392,"A4":440,"B4":494,
    "C5":523,"D5":587,"E5":659,"F5":698,"G5":784,"A5":880,"B5":988,
    "C6":1047,"G3":196,"REST":0,
}

# Westminster quarter chime (4 notes)
_WESTMINSTER = [
    ("E5",400),("C5",400),("D5",400),("G4",800),
]

# 8-bit fanfare
_8BIT = [
    ("C5",100),("E5",100),("G5",100),("C6",200),("REST",80),
    ("G5",100),("C6",300),
]

# ── State ────────────────────────────────────────────────
_last_chime_hour = -1
_tick_phase      = True   # alternates for tick/tock

def init():
    print("[chime] init, style={}".format(config.CHIME_STYLE))

# ─────────────────────────────────────────────────────────
#  TICK  (called every 1 s from main loop)
# ─────────────────────────────────────────────────────────
def tick():
    global _last_chime_hour, _tick_phase

    h = clock.hour()
    m = clock.minute()
    s = clock.second()

    # Tick-tock every second
    if config.CHIME_STYLE == "ticktock" and _HW:
        if not _in_quiet_hours(h):
            freq = 800 if _tick_phase else 600
            speaker.tone(freq, 30)
            _tick_phase = not _tick_phase

    # Hourly chime — fire at XX:00:02 to avoid racing the minute tick
    if m == 0 and s == 2 and h != _last_chime_hour:
        if not _in_quiet_hours(h):
            _last_chime_hour = h
            play_hour_chime(h)

def play_hour_chime(hour_24):
    if not _HW or config.CHIME_STYLE in ("none", "ticktock"):
        return
    style = config.CHIME_STYLE
    print("[chime] Playing {} chime for hour {}".format(style, hour_24))
    if   style == "westminster": _play_sequence(_WESTMINSTER)
    elif style == "8bit":        _play_sequence(_8BIT)

def play_preview():
    """Soft 2-note preview 2 min before alarm."""
    if not _HW:
        return
    _play_sequence([("G4", 200), ("C5", 300)])

# ─────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────
def _play_sequence(seq):
    if not _HW:
        return
    for note, dur in seq:
        freq = NOTE.get(note, 0)
        if freq:
            speaker.tone(freq, dur)
        else:
            utime.sleep_ms(dur)
        utime.sleep_ms(40)   # gap between notes

def _in_quiet_hours(h):
    qs = config.CHIME_QUIET_START
    qe = config.CHIME_QUIET_END
    if qs > qe:   # wraps midnight (e.g. 22 → 7)
        return h >= qs or h < qe
    return qs <= h < qe
