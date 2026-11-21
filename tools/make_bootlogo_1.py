#!/usr/bin/env python3
"""Create the RG DS Plus startup control guide with Noto Sans JP Bold."""
from pathlib import Path
import struct

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = ROOT / 'fonts/NotoSansJP-Bold.ttf'
SIZE = (1024, 768)


def save_top_down_bmp(image: Image.Image, path: Path) -> None:
    image = image.convert('RGB')
    width, height = image.size
    stride = (width * 3 + 3) & ~3
    rgb = image.tobytes()
    pixels = bytearray()
    for y in range(height):
        row = rgb[y * width * 3:(y + 1) * width * 3]
        bgr = bytearray(len(row))
        bgr[0::3], bgr[1::3], bgr[2::3] = row[2::3], row[1::3], row[0::3]
        pixels.extend(bgr)
        pixels.extend(b'\0' * (stride - len(bgr)))
    offset = 54
    header = struct.pack('<2sIHHI', b'BM', offset + len(pixels), 0, 0, offset)
    dib = struct.pack('<IiiHHIIiiII', 40, width, -height, 1, 24, 0,
                      len(pixels), 2834, 2834, 0, 0)
    path.write_bytes(header + dib + pixels)


def main() -> None:
    image = Image.new('RGB', SIZE, (38, 38, 38))
    draw = ImageDraw.Draw(image)

    def draw_shadowed(position, text, font, color):
        x, y = position
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
        draw.text(position, text, font=font, fill=color)
    brand = ImageFont.truetype(str(FONT_PATH), 30)
    title = ImageFont.truetype(str(FONT_PATH), 42)
    label_font = ImageFont.truetype(str(FONT_PATH), 26)
    action_font = ImageFont.truetype(str(FONT_PATH), 38)

    draw_shadowed((20, 18), 'DS RGDSPLUS JP+', brand, (187, 187, 187))
    draw_shadowed((20, 58), 'CONTROLS', title, (255, 255, 255))

    controls = [
        ('IN-GAME MENU', 'MENU', 44, 220),
        ('HI-RES MODE', 'MENU + START', 44, 355),
        ('SWAP SCREENS', 'MENU + SELECT', 44, 490),
        ('SYSTEM MENU', 'MENU AGAIN', 540, 220),
        ('SCREENSHOT', 'MENU + A', 540, 355),
        ('FAST-FORWARD', 'BACK', 540, 490),
    ]
    for label, action, x, y in controls:
        draw_shadowed((x, y), label, label_font, (187, 187, 187))
        draw_shadowed((x, y + 34), action, action_font, (255, 255, 255))

    save_top_down_bmp(image, ROOT / 'skeleton/bootlogo-1.bmp')
    image.save(ROOT / 'github/bootlogo-1-preview.png')


if __name__ == '__main__':
    main()
