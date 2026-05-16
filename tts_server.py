import socket
import os
from flask import Flask, request, send_file, Response
from gtts import gTTS
import io

app = Flask(__name__)


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


@app.route("/speak")
def speak():
    text = request.args.get("text", "").replace("+", " ")
    if not text:
        return "No text provided", 400
    print(f"[TTS] Speaking: {text[:80]}...")
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return Response(buf.read(), mimetype="audio/mpeg")
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return f"TTS error: {e}", 500


@app.route("/alarm.mp3")
def alarm_mp3():
    """
    Optional: put an alarm.mp3 file in the same folder as this script
    and set ALARM_AUDIO_URL = "http://YOUR_IP:5001/alarm.mp3" in main.py
    """
    path = os.path.join(os.path.dirname(__file__), "alarm.mp3")
    if os.path.exists(path):
        return send_file(path, mimetype="audio/mpeg")
    return "alarm.mp3 not found", 404


@app.route("/")
def index():
    return (
        "<h2>TTS Server Running</h2>"
        "<p>Test: <a href='/speak?text=Hello+world'>/speak?text=Hello+world</a></p>"
    )


if __name__ == "__main__":
    ip = get_local_ip()
    print("=" * 50)
    print(f"  TTS Server starting on http://{ip}:5001")
    print(f"  Set TTS_SERVER_IP = \"{ip}\" in main.py")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=False)
