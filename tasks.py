import utime
import config
import agent

# Seconds logged per task label (Coding, Email, …)
_totals = {}
_active_label   = ""
_active_since   = 0
_tracking       = False


def init():
    for label in config.TASK_BY_ORIENTATION.values():
        _totals.setdefault(label, 0)
    print("[tasks] init", list(_totals.keys()))


def on_orientation(orient):
    """Called when IMU confirms a new orientation."""
    global _active_label, _active_since, _tracking

    label = config.TASK_BY_ORIENTATION.get(orient, "")
    if not label:
        return

    _flush()

    _active_label = label
    _active_since = utime.time()
    _tracking     = True
    print("[tasks] tracking:", label)

    import pomodoro
    if (config.POMODORO_AUTO_START_ON_FLIP and
            pomodoro.state() == pomodoro.STATE_IDLE):
        pomodoro.start_work()


def current_label():
    return _active_label


def is_tracking():
    return _tracking


def should_track_time():
    """Accumulate task time during pomodoro work or when idle."""
    import pomodoro
    if pomodoro.state() == pomodoro.STATE_BREAK:
        return False
    if pomodoro.state() == pomodoro.STATE_WORK:
        return True
    return _tracking


def tick():
    """Periodic flush of partial seconds to totals + agent."""
    if not _tracking or not _active_label:
        return
    if not should_track_time():
        return
    # Totals updated on orientation change / flush; nothing per-second here.


def _flush():
    global _active_label, _active_since, _tracking

    if not _tracking or not _active_label or _active_since <= 0:
        return

    elapsed = utime.time() - _active_since
    if elapsed <= 0:
        return

    prev = _totals.get(_active_label, 0)
    _totals[_active_label] = prev + elapsed
    agent.post_track(_active_label, elapsed)

    _active_since = utime.time()
    print("[tasks] +{}s → {} (total {}s)".format(
        elapsed, _active_label, _totals[_active_label]))


def flush():
    _flush()


def totals():
    return dict(_totals)


def total_for(label):
    return _totals.get(label, 0)
