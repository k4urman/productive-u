import urequests
import config
import clock

_events = []


def fetch():
    global _events
    try:
        r   = urequests.get(config.GCAL_ICS_URL, timeout=15)
        ics = r.text
        r.close()
        _events = _parse(ics)
        print("[calendar] {} events today".format(len(_events)))
    except Exception as e:
        print("[calendar] Error:", e)


def _parse(ics_text):
    lt    = clock.local_time()
    today = "{:04d}{:02d}{:02d}".format(lt[0], lt[1], lt[2])
    events = []
    in_ev  = False
    summary = ""
    dtstart = ""
    for line in ics_text.split("\n"):
        line = line.strip()
        if line == "BEGIN:VEVENT":
            in_ev = True
            summary = ""
            dtstart = ""
        elif line == "END:VEVENT":
            if in_ev and today in dtstart:
                try:
                    tp = dtstart.split("T")[1][:4]
                    h  = (int(tp[:2]) + config.TZ_UTC_OFFSET) % 24
                    m  = tp[2:]
                    events.append("{} at {:02d}:{}".format(summary, h, m))
                except Exception:
                    if summary:
                        events.append(summary)
            in_ev = False
        elif in_ev:
            if line.startswith("SUMMARY:"):
                summary = line[8:]
            elif line.startswith("DTSTART"):
                dtstart = line.split(":")[-1]
    return events


def get_events():
    return _events


def next_event_str():
    return _events[0] if _events else ""
