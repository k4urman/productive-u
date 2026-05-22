import utime
import modes

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

# ── State ─────────────────────────────────────────────────
_current_orient  = "portrait"   # last confirmed orientation
_candidate       = "portrait"   # orientation being held
_candidate_since = 0            # when candidate was first detected
_HOLD_MS         = 1000         # ms to hold before confirming

_ORIENT_TO_MODE = {
    "portrait":          modes.MODE_CLOCK,
    "landscape_right":   modes.MODE_TIMER,
    "portrait_inverted": modes.MODE_KITCHEN,
    "landscape_left":    modes.MODE_WEATHER,
}

_LCD_ROTATION = {
    "portrait":          0,
    "landscape_right":   1,
    "portrait_inverted": 2,
    "landscape_left":    3,
}

def init():
    print("[imu] init")
    _set_lcd_rotation("portrait")

# ─────────────────────────────────────────────────────────
#  TICK  (called every 200 ms)
# ─────────────────────────────────────────────────────────
def tick():
    global _current_orient, _candidate, _candidate_since

    if not _HW:
        return

    orient = _read_orientation()
    if orient is None:
        return

    now = utime.ticks_ms()

    if orient != _candidate:
        # New candidate — start hold timer
        _candidate       = orient
        _candidate_since = now
    else:
        # Same candidate — check if held long enough
        if (orient != _current_orient and
                utime.ticks_diff(now, _candidate_since) >= _HOLD_MS):
            _current_orient = orient
            _set_lcd_rotation(orient)
            new_mode = _ORIENT_TO_MODE.get(orient, modes.MODE_CLOCK)
            modes.set_mode(new_mode)
            print("[imu] Orientation:", orient, "→ mode:", new_mode)

# ─────────────────────────────────────────────────────────
#  ORIENTATION DETECTION
# ─────────────────────────────────────────────────────────
def _read_orientation():
    """
    Returns one of: portrait | portrait_inverted |
                    landscape_right | landscape_left
    Based on which axis has the largest gravity component.
    """
    try:
        ax, ay, az = _imu_hw.acceleration
    except Exception:
        return None

    abs_x = abs(ax)
    abs_y = abs(ay)
    abs_z = abs(az)

    # Only classify if device is roughly flat to an axis (not tumbling)
    if abs_z > abs_x and abs_z > abs_y:
        # Flat on table — keep current orientation
        return _current_orient

    if abs_y >= abs_x:
        # Portrait orientations
        return "portrait" if ay > 0 else "portrait_inverted"
    else:
        # Landscape orientations
        return "landscape_right" if ax > 0 else "landscape_left"

# ─────────────────────────────────────────────────────────
#  LCD ROTATION
# ─────────────────────────────────────────────────────────
def _set_lcd_rotation(orient):
    if not _LCD:
        return
    rot = _LCD_ROTATION.get(orient, 0)
    try:
        lcd.setRotation(rot)
    except Exception as e:
        print("[imu] setRotation failed:", e)
