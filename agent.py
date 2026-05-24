import ujson
import urequests
import config

_status = {
    "mic_hot":     False,
    "render_done": False,
}
_agent_ok = False


def _base_url():
    return "http://{}:{}".format(config.AGENT_IP, config.AGENT_PORT)


def send_macro(action, layer=""):
    if not action:
        return False
    url  = _base_url() + "/macro"
    body = ujson.dumps({"action": action, "layer": layer})
    try:
        r = urequests.post(url, data=body,
                           headers={"Content-Type": "application/json"},
                           timeout=4)
        ok = r.status_code == 200
        r.close()
        print("[agent] macro", action, "→", ok)
        return ok
    except Exception as e:
        print("[agent] macro error:", e)
        return False


def post_track(category, seconds):
    if seconds <= 0:
        return
    url  = _base_url() + "/track"
    body = ujson.dumps({"category": category, "seconds": int(seconds)})
    try:
        r = urequests.post(url, data=body,
                           headers={"Content-Type": "application/json"},
                           timeout=4)
        r.close()
    except Exception as e:
        print("[agent] track error:", e)


def fetch_status():
    global _status, _agent_ok
    url = _base_url() + "/status"
    try:
        r = urequests.get(url, timeout=3)
        if r.status_code == 200:
            data = ujson.loads(r.text)
            _status["mic_hot"]     = bool(data.get("mic_hot", False))
            _status["render_done"] = bool(data.get("render_done", False))
            _agent_ok = True
        r.close()
    except Exception as e:
        _agent_ok = False
        print("[agent] status error:", e)


def get_status():
    return _status


def agent_reachable():
    return _agent_ok


def ack_render_done():
    url = _base_url() + "/status/ack"
    try:
        r = urequests.post(url, timeout=2)
        r.close()
    except Exception:
        pass
