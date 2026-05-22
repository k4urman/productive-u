import utime
import ntptime
import config

# ── State ────────────────────────────────────────────────
_dst_active  = False
_tz_offset   = config.TZ_UTC_OFFSET   # current effective offset (with DST)
_last_sync   = 0
SYNC_INTERVAL = 3600 * 6   # re-sync NTP every 6 hours

def init():
    _ntp_sync()
    _update_dst()

# ─────────────────────────────────────────────────────────
#  NTP SYNC
# ─────────────────────────────────────────────────────────
def _ntp_sync():
    global _last_sync
    for attempt in range(3):
        try:
            ntptime.settime()   # sets RTC to UTC
            _last_sync = utime.time()
            print("[clock] NTP synced")
            return True
        except Exception as e:
            print("[clock] NTP attempt {} failed: {}".format(attempt + 1, e))
            utime.sleep(2)
    print("[clock] NTP sync failed — using RTC time")
    return False

def tick_sync():
    """Call periodically; re-syncs NTP every SYNC_INTERVAL seconds."""
    if utime.time() - _last_sync > SYNC_INTERVAL:
        _ntp_sync()
        _update_dst()

# ─────────────────────────────────────────────────────────
#  DST CALCULATION
# ─────────────────────────────────────────────────────────
def _nth_sunday(year, month, n):
    """Return day-of-month for the Nth Sunday of a given month/year."""
    # Find first Sunday
    import utime
    # Jan 1 of year — use mktime trick
    t = utime.mktime((year, month, 1, 0, 0, 0, 0, 0))
    weekday = utime.localtime(t)[6]   # 0=Mon … 6=Sun
    first_sunday = 1 + (6 - weekday) % 7
    return first_sunday + (n - 1) * 7

def _update_dst():
    global _dst_active, _tz_offset
    if not config.DST_ENABLED:
        _tz_offset = config.TZ_UTC_OFFSET
        _dst_active = False
        return

    utc  = utime.localtime(utime.time())
    year = utc[0]
    month= utc[1]
    day  = utc[2]

    dst_start_day = _nth_sunday(year, config.DST_START_MONTH, config.DST_START_WEEK)
    dst_end_day   = _nth_sunday(year, config.DST_END_MONTH,   config.DST_END_WEEK)

    # DST is active between start and end (Northern Hemisphere assumption)
    after_start = (month > config.DST_START_MONTH or
                   (month == config.DST_START_MONTH and day >= dst_start_day))
    before_end  = (month < config.DST_END_MONTH or
                   (month == config.DST_END_MONTH and day < dst_end_day))

    _dst_active = after_start and before_end
    _tz_offset  = config.TZ_UTC_OFFSET + (config.DST_OFFSET if _dst_active else 0)
    print("[clock] DST active:", _dst_active, "| Effective UTC offset:", _tz_offset)

# ─────────────────────────────────────────────────────────
#  PUBLIC ACCESSORS
# ─────────────────────────────────────────────────────────
def local_time():
    """Return localtime tuple adjusted for timezone + DST."""
    t = utime.time() + _tz_offset * 3600
    return utime.localtime(t)

def time_str():
    lt = local_time()
    return "{:02d}:{:02d}:{:02d}".format(lt[3], lt[4], lt[5])

def time_hhmm():
    lt = local_time()
    return "{:02d}:{:02d}".format(lt[3], lt[4])

def date_str():
    lt = local_time()
    days   = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    months = ["","Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    return "{} {} {}  {}".format(days[lt[6]], months[lt[1]], lt[2], lt[0])

def hour():
    return local_time()[3]

def minute():
    return local_time()[4]

def second():
    return local_time()[5]

def is_dst():
    return _dst_active

def epoch():
    return utime.time()
