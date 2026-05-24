import utime
import config

STATE_IDLE  = "idle"
STATE_WORK  = "work"
STATE_BREAK = "break"

_state           = STATE_IDLE
_remaining       = 0
_running         = False
_last_tick       = 0
_completed_work  = 0   # pomodoros finished today (simple counter)

WORK_SEC  = config.POMODORO_WORK_MINUTES * 60
BREAK_SEC = config.POMODORO_BREAK_MINUTES * 60


def init():
    global _remaining
    _remaining = WORK_SEC
    print("[pomodoro] init work={}m break={}m".format(
        config.POMODORO_WORK_MINUTES, config.POMODORO_BREAK_MINUTES))


def state():
    return _state

def is_active():
    return _state != STATE_IDLE

def is_running():
    return _running and _state != STATE_IDLE

def remaining():
    _tick()
    return max(0, _remaining)

def completed_work():
    return _completed_work


def start_work():
    global _state, _remaining, _running, _last_tick
    _state     = STATE_WORK
    _remaining = WORK_SEC
    _running   = True
    _last_tick = utime.ticks_ms()
    print("[pomodoro] work started")


def start_break():
    global _state, _remaining, _running, _last_tick
    _state     = STATE_BREAK
    _remaining = BREAK_SEC
    _running   = True
    _last_tick = utime.ticks_ms()
    print("[pomodoro] break started")


def toggle_pause():
    global _running, _last_tick
    if _state == STATE_IDLE:
        start_work()
        return
    _running = not _running
    if _running:
        _last_tick = utime.ticks_ms()
    print("[pomodoro] running:", _running)


def skip_phase():
    """End current phase and move to the next."""
    global _completed_work
    if _state == STATE_WORK:
        _completed_work += 1
        _finish_work_block()
    elif _state == STATE_BREAK:
        start_work()
    elif _state == STATE_IDLE:
        start_work()


def stop():
    global _state, _running, _remaining
    _state     = STATE_IDLE
    _running   = False
    _remaining = WORK_SEC
    print("[pomodoro] stopped")


def tick():
    _tick()


def _tick():
    global _remaining, _running, _last_tick, _state, _completed_work

    if not _running or _state == STATE_IDLE:
        return

    now     = utime.ticks_ms()
    elapsed = utime.ticks_diff(now, _last_tick) // 1000
    if elapsed < 1:
        return

    _remaining -= elapsed
    _last_tick  = now

    if _remaining <= 0:
        if _state == STATE_WORK:
            _completed_work += 1
            _finish_work_block()
        else:
            start_work()


def _finish_work_block():
    import tasks
    tasks.flush()
    _play_chime()
    start_break()


def _play_chime():
    try:
        from m5stack import speaker
        speaker.tone(880, 150)
        utime.sleep_ms(180)
        speaker.tone(1100, 200)
    except Exception:
        pass


def phase_label():
    if _state == STATE_WORK:
        return "FOCUS"
    if _state == STATE_BREAK:
        return "BREAK"
    return "READY"
