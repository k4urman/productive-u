import utime
import os
import config

try:
    from machine import ADC, Pin
    _madc = ADC(Pin(34))
    _madc.atten(ADC.ATTN_11DB)
    _MIC_OK = True
except Exception:
    _MIC_OK = False

_recording   = False
_samples     = []
_started_ms  = 0


def is_recording():
    return _recording


def start():
    global _recording, _samples, _started_ms
    if not _MIC_OK:
        print("[memo] mic unavailable")
        return False
    _ensure_dir()
    _samples    = []
    _recording  = True
    _started_ms = utime.ticks_ms()
    print("[memo] recording...")
    return True


def stop():
    global _recording
    if not _recording:
        return None

    _recording = False
    path = _save_wav()
    print("[memo] saved", path, "samples:", len(_samples))
    _samples = []
    return path


def tick_sample():
    """Call frequently while recording (e.g. every main-loop pass)."""
    if not _recording or not _MIC_OK:
        return
    # ~8 kHz target: sample when ~125 us passed (coarse on MicroPython loop)
    if len(_samples) < 8000 * 120:   # cap ~2 min
        _samples.append(_madc.read())


def _ensure_dir():
    try:
        os.mkdir(config.MEMO_DIR)
    except OSError:
        pass
    except Exception as e:
        print("[memo] mkdir failed:", e)


def _save_wav():
    lt = utime.localtime()
    name = config.MEMO_DIR + "/{:04d}{:02d}{:02d}-{:02d}{:02d}{:02d}.wav".format(
        lt[0], lt[1], lt[2], lt[3], lt[4], lt[5])

    rate     = config.MEMO_SAMPLE_RATE
    raw      = _samples
    n        = len(raw)
    if n == 0:
        return None

    # Normalize 12-bit ADC to 16-bit PCM
    pcm = bytearray(n * 2)
    for i, v in enumerate(raw):
        s = int((v - 2048) * 16)
        if s > 32767:
            s = 32767
        if s < -32768:
            s = -32768
        pcm[i * 2]     = s & 0xFF
        pcm[i * 2 + 1] = (s >> 8) & 0xFF

    data_size = len(pcm)
    byte_rate = rate * 2
    try:
        f = open(name, "wb")
        f.write(b"RIFF")
        f.write(_le32(36 + data_size))
        f.write(b"WAVEfmt ")
        f.write(_le32(16))
        f.write(_le16(1))
        f.write(_le16(1))
        f.write(_le32(rate))
        f.write(_le32(byte_rate))
        f.write(_le16(2))
        f.write(_le16(16))
        f.write(b"data")
        f.write(_le32(data_size))
        f.write(pcm)
        f.close()
        return name
    except Exception as e:
        print("[memo] save failed:", e)
        return None


def _le16(v):
    return bytes([v & 0xFF, (v >> 8) & 0xFF])


def _le32(v):
    return bytes([v & 0xFF, (v >> 8) & 0xFF, (v >> 16) & 0xFF, (v >> 24) & 0xFF])
