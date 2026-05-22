import sys
import os
import struct
from PIL import Image

SCREEN_W = 320
SCREEN_H = 240

def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

def convert(gif_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(gif_path)
    frame_idx = 0
    try:
        while True:
            frame = img.convert("RGB").resize((SCREEN_W, SCREEN_H), Image.LANCZOS)
            out_path = os.path.join(out_dir, f"frame_{frame_idx:03d}.rgb")
            with open(out_path, "wb") as f:
                for y in range(SCREEN_H):
                    for x in range(SCREEN_W):
                        r, g, b = frame.getpixel((x, y))
                        px = rgb888_to_rgb565(r, g, b)
                        f.write(struct.pack("<H", px))
            print(f"  Frame {frame_idx:03d} → {out_path}")
            frame_idx += 1
            img.seek(img.tell() + 1)
    except EOFError:
        pass
    print(f"\nDone. {frame_idx} frames written to {out_dir}")
    print(f'Set GIF_BACKGROUND = "/sd/{os.path.basename(out_dir)}"  in config.py')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python gif_to_frames.py input.gif output_dir/")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
