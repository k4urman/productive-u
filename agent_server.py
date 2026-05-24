"""
Productive-U PC agent — run on your laptop (same WiFi as M5Stack).

    pip install flask
    python agent_server.py

Set AGENT_IP in config.py to the IP this script prints.
"""
import io
import json
import os
import socket
import time
from collections import defaultdict

from flask import Flask, request, jsonify, Response

app = Flask(__name__)

_track_log = defaultdict(int)
_status = {
    "mic_hot": False,
    "render_done": False,
}

# Extend these handlers for real OS integration (pynput, AutoHotkey, etc.)
def _run_macro(action, layer):
    print("[macro] layer={} action={}".format(layer, action))
    # Example Windows media keys via PowerShell (optional):
    # if action == "media_next":
    #     os.system('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"')
    return True


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


@app.route("/macro", methods=["POST"])
def macro():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "")
    layer  = data.get("layer", "")
    if not action:
        return jsonify({"ok": False, "error": "no action"}), 400
    ok = _run_macro(action, layer)
    return jsonify({"ok": ok, "action": action})


@app.route("/track", methods=["POST"])
def track():
    data = request.get_json(silent=True) or {}
    cat = data.get("category", "")
    sec = int(data.get("seconds", 0))
    if cat and sec > 0:
        _track_log[cat] += sec
        print("[track] +{}s {} (total {}s)".format(sec, cat, _track_log[cat]))
    return jsonify({"ok": True})


@app.route("/status", methods=["GET"])
def status():
    # Plug in real mic detection here; demo toggles via query for testing:
    # GET /status?mic_hot=1
    if request.args.get("mic_hot") == "1":
        _status["mic_hot"] = True
    if request.args.get("mic_hot") == "0":
        _status["mic_hot"] = False
    if request.args.get("render_done") == "1":
        _status["render_done"] = True
    return jsonify(_status)


@app.route("/status/ack", methods=["POST"])
def status_ack():
    _status["render_done"] = False
    return jsonify({"ok": True})


@app.route("/track/log", methods=["GET"])
def track_log():
    return jsonify(dict(_track_log))


@app.route("/speak")
def speak():
    """Optional TTS (requires gTTS): /speak?text=hello"""
    text = request.args.get("text", "").replace("+", " ").strip()
    if not text:
        return "No text", 400
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return Response(buf.read(), mimetype="audio/mpeg")
    except ImportError:
        return "Install gTTS for /speak", 501
    except Exception as e:
        return str(e), 500


@app.route("/")
def index():
    ip = local_ip()
    return (
        "<h2>Productive-U Agent</h2>"
        "<p>IP: <code>{}</code> — set AGENT_IP in config.py</p>"
        "<ul>"
        "<li>POST /macro JSON {{action, layer}}</li>"
        "<li>GET /status — mic_hot, render_done</li>"
        "<li>POST /track JSON {{category, seconds}}</li>"
        "<li>GET /track/log</li>"
        "<li>Test LEDs: <a href='/status?mic_hot=1'>mic on</a> "
        "<a href='/status?mic_hot=0'>mic off</a> "
        "<a href='/status?render_done=1'>render done</a></li>"
        "</ul>".format(ip)
    )


if __name__ == "__main__":
    ip = local_ip()
    print("=" * 55)
    print("  Productive-U Agent  →  http://{}:5001".format(ip))
    print('  Set AGENT_IP = "{}"  in config.py'.format(ip))
    print("=" * 55)
    app.run(host="0.0.0.0", port=5001, debug=False)
