# Deprecated: use agent_server.py for Productive-U. Kept for /speak TTS only.
import io
import os
import socket
from flask import Flask, request, Response, send_file
from gtts import gTTS

app = Flask(__name__)

def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

@app.route("/speak")
def speak():
    text = request.args.get("text", "").replace("+", " ").strip()
    if not text:
        return "No text", 400
    print(f"[TTS] {text[:80]}{'...' if len(text)>80 else ''}")
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return Response(buf.read(), mimetype="audio/mpeg")
    except Exception as e:
        print(f"[TTS] Error: {e}")
        return f"Error: {e}", 500

@app.route("/alarm.mp3")
def alarm():
    path = os.path.join(os.path.dirname(__file__), "alarm.mp3")
    if os.path.exists(path):
        return send_file(path, mimetype="audio/mpeg")
    return "alarm.mp3 not found — place one next to tts_server.py", 404

@app.route("/")
def index():
    ip = local_ip()
    return (f"<h2>TTS Server OK</h2>"
            f"<p>Set <code>TTS_SERVER_IP = \"{ip}\"</code> in config.py</p>"
            f"<p>Test: <a href='/speak?text=Good+morning'>/speak?text=Good+morning</a></p>")

if __name__ == "__main__":
    ip = local_ip()
    print("=" * 55)
    print(f"  TTS Server  →  http://{ip}:5001")
    print(f"  Set TTS_SERVER_IP = \"{ip}\"  in config.py")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5001, debug=False)
