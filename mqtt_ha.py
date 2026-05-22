import config

try:
    from umqtt.simple import MQTTClient
    _MQTT_AVAILABLE = True
except ImportError:
    print("[mqtt] umqtt not available — MQTT disabled")
    _MQTT_AVAILABLE = False

_client   = None
_connected= False
_data = {
    "indoor_temp": "",
    "aqi":         "",
    "doorbell":    "",
    "next_event":  "",
}

# ─────────────────────────────────────────────────────────
#  CONNECT
# ─────────────────────────────────────────────────────────
def connect():
    global _client, _connected
    if not config.MQTT_ENABLED or not _MQTT_AVAILABLE:
        return
    try:
        _client = MQTTClient(
            client_id = config.MQTT_CLIENT_ID,
            server    = config.MQTT_BROKER,
            port      = config.MQTT_PORT,
            user      = config.MQTT_USER     or None,
            password  = config.MQTT_PASSWORD or None,
            keepalive = 60,
        )
        _client.set_callback(_on_message)
        _client.connect()
        _subscribe()
        _connected = True
        print("[mqtt] Connected to", config.MQTT_BROKER)
    except Exception as e:
        print("[mqtt] Connect failed:", e)
        _connected = False

def _subscribe():
    topics = [
        config.MQTT_TOPIC_INDOOR_TEMP,
        config.MQTT_TOPIC_AQI,
        config.MQTT_TOPIC_DOORBELL,
        config.MQTT_TOPIC_NEXT_EVENT,
    ]
    for t in topics:
        if t:
            _client.subscribe(t.encode())

# ─────────────────────────────────────────────────────────
#  TICK  (called every 500 ms)
# ─────────────────────────────────────────────────────────
def tick():
    global _connected
    if not config.MQTT_ENABLED or not _MQTT_AVAILABLE or not _client:
        return
    try:
        _client.check_msg()   # non-blocking
    except Exception as e:
        print("[mqtt] tick error:", e)
        _connected = False
        _reconnect()

def _reconnect():
    global _connected
    try:
        _client.connect()
        _subscribe()
        _connected = True
        print("[mqtt] Reconnected")
    except Exception:
        pass

# ─────────────────────────────────────────────────────────
#  MESSAGE CALLBACK
# ─────────────────────────────────────────────────────────
def _on_message(topic, msg):
    topic = topic.decode()
    value = msg.decode().strip()
    print("[mqtt] {} = {}".format(topic, value))

    if topic == config.MQTT_TOPIC_INDOOR_TEMP:
        _data["indoor_temp"] = value
    elif topic == config.MQTT_TOPIC_AQI:
        _data["aqi"] = value
    elif topic == config.MQTT_TOPIC_DOORBELL:
        # "ON" triggers an alert; auto-clears after display picks it up
        _data["doorbell"] = "DOORBELL!" if value == "ON" else ""
    elif topic == config.MQTT_TOPIC_NEXT_EVENT:
        _data["next_event"] = value

# ─────────────────────────────────────────────────────────
#  PUBLIC
# ─────────────────────────────────────────────────────────
def get_data():
    return _data

def is_connected():
    return _connected
