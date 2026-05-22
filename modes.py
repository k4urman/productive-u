import utime

MODE_CLOCK   = "clock"
MODE_TIMER   = "timer"
MODE_KITCHEN = "kitchen"
MODE_WEATHER = "weather"

_mode = MODE_CLOCK

# ── Countdown timer state ────────────────────────────────
_TIMER_DEFAULT_SECONDS = 5 * 60   # 5 minutes
_timer_target   = _TIMER_DEFAULT_SECONDS
_timer_remaining= _TIMER_DEFAULT_SECONDS
_timer_running  = False
_timer_last_tick= 0

# ── Kitchen stopwatch state ──────────────────────────────
_KITCHEN_DEFAULT_SECONDS = 10 * 60   # 10 minutes
_kitchen_target  = _KITCHEN_DEFAULT_SECONDS
_kitchen_elapsed = 0
_kitchen_running = False
_kitchen_last_tick = 0

# ─────────────────────────────────────────────────────────
#  MODE SWITCHING
# ─────────────────────────────────────────────────────────
def set_mode(m):
    global _mode
    _mode = m
    print("[modes] Mode →", m)

def current():
    return _mode

# ─────────────────────────────────────────────────────────
#  COUNTDOWN TIMER
# ─────────────────────────────────────────────────────────
def timer_start_stop():
    global _timer_running, _timer_last_tick
    _timer_running = not _timer_running
    if _timer_running:
        _timer_last_tick = utime.ticks_ms()
    print("[modes] Timer running:", _timer_running)

def timer_reset():
    global _timer_remaining, _timer_running
    _timer_running   = False
    _timer_remaining = _timer_target

def timer_remaining():
    _tick_timer()
    return max(0, _timer_remaining)

def timer_set_minutes(m):
    global _timer_target, _timer_remaining
    _timer_target    = m * 60
    _timer_remaining = _timer_target

def _tick_timer():
    global _timer_remaining, _timer_running, _timer_last_tick
    if not _timer_running:
        return
    now     = utime.ticks_ms()
    elapsed = utime.ticks_diff(now, _timer_last_tick) // 1000
    if elapsed >= 1:
        _timer_remaining -= elapsed
        _timer_last_tick  = now
        if _timer_remaining <= 0:
            _timer_remaining = 0
            _timer_running   = False
            _timer_alarm()

def _timer_alarm():
    print("[modes] Timer finished!")
    try:
        from m5stack import speaker
        notes = [784, 659, 523, 659, 784]
        import utime as ut
        for n in notes:
            speaker.tone(n, 200)
            ut.sleep_ms(250)
    except Exception:
        pass

# ─────────────────────────────────────────────────────────
#  KITCHEN STOPWATCH
# ─────────────────────────────────────────────────────────
def kitchen_start_stop():
    global _kitchen_running, _kitchen_last_tick
    _kitchen_running = not _kitchen_running
    if _kitchen_running:
        _kitchen_last_tick = utime.ticks_ms()
    print("[modes] Kitchen running:", _kitchen_running)

def kitchen_reset():
    global _kitchen_elapsed, _kitchen_running
    _kitchen_running = False
    _kitchen_elapsed = 0

def kitchen_elapsed():
    _tick_kitchen()
    return _kitchen_elapsed

def kitchen_target():
    return _kitchen_target

def kitchen_set_minutes(m):
    global _kitchen_target
    _kitchen_target = m * 60

def _tick_kitchen():
    global _kitchen_elapsed, _kitchen_running, _kitchen_last_tick
    if not _kitchen_running:
        return
    now     = utime.ticks_ms()
    elapsed = utime.ticks_diff(now, _kitchen_last_tick) // 1000
    if elapsed >= 1:
        _kitchen_elapsed += elapsed
        _kitchen_last_tick = now
        if _kitchen_elapsed >= _kitchen_target:
            _kitchen_running = False
            _kitchen_alarm()

def _kitchen_alarm():
    print("[modes] Kitchen timer done!")
    try:
        from m5stack import speaker
        import utime as ut
        for _ in range(3):
            speaker.tone(880, 300)
            ut.sleep_ms(350)
            speaker.tone(660, 300)
            ut.sleep_ms(350)
    except Exception:
        pass
