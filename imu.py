import utime
import tasks

try:
    from m5stack import imu as _imu_hw
    _HW = True
except Exception:
    print("[imu] IMU hardware not available")
    _HW = False

try:
    from m5stack import lcd
    _LCD = True
except Exception:
    _LCD = False

_current_orient  = "portrait"
_candidate       = "portrait"
_candidate_since = 0
_HOLD_MS         = 1000

_LCD_ROTATION = {
    "portrait":          0,
    "landscape_right":   1,
    "portrait_inverted": 2,
    "landscape_left":    3,
}


def init():
    print("[imu] init")
    _set_lcd_rotation("portrait")


def tick():
    global _current_orient, _candidate, _candidate_since

    if not _HW:
        return

    orient = _read_orientation()
    if orient is None:
        return

    now = utime.ticks_ms()

    if orient != _candidate:
        _candidate       = orient
        _candidate_since = now
    else:
        if (orient != _current_orient and
                utime.ticks_diff(now, _candidate_since) >= _HOLD_MS):
            _current_orient = orient
            _set_lcd_rotation(orient)
            tasks.on_orientation(orient)
            print("[imu] orientation:", orient)


def current_orientation():
    return _current_orient


def _read_orientation():
    try:
        ax, ay, az = _imu_hw.acceleration
    except Exception:
        return None

    abs_x = abs(ax)
    abs_y = abs(ay)
    abs_z = abs(az)

    if abs_z > abs_x and abs_z > abs_y:
        return _current_orient

    if abs_y >= abs_x:
        return "portrait" if ay > 0 else "portrait_inverted"
    return "landscape_right" if ax > 0 else "landscape_left"


def _set_lcd_rotation(orient):
    if not _LCD:
        return
    rot = _LCD_ROTATION.get(orient, 0)
    try:
        lcd.setRotation(rot)
    except Exception as e:
        print("[imu] setRotation failed:", e)
