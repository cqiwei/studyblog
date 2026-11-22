"""生成站点图标：static/favicon.ico + apple-touch-icon.png + favicon-*.png

纯 Pillow 绘制，可重复执行。设计：圆角方块 + 渐变底 + 白色「蔚」字。
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
PREVIEW = ROOT / ".deploy" / "previews"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_SERIF = "C:/Windows/Fonts/simsun.ttc"

S = 1024  # 超采样画布


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, c1, c2, angle=135):
    """线性渐变。"""
    w = h = size
    img = Image.new("RGB", (w, h))
    px = img.load()
    rad = math.radians(angle)
    dx, dy = math.cos(rad), math.sin(rad)
    scale = abs(dx) * w + abs(dy) * h
    for y in range(h):
        for x in range(w):
            t = ((x * dx + y * dy) / scale) + (0.5 - (0.5 * (abs(dx) + abs(dy))) + 0.5)
            t = min(1.0, max(0.0, t))
            px[x, y] = lerp(c1, c2, t)
    return img


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return m


def build():
    # 底色：深靛 → 紫 → 青，和站点极光呼应
    base = gradient(S, (26, 27, 58), (88, 60, 168), angle=125).convert("RGBA")
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((S * 0.42, -S * 0.18, S * 1.12, S * 0.52), fill=(64, 208, 226, 150))
    gd.ellipse((-S * 0.22, S * 0.55, S * 0.55, S * 1.12), fill=(255, 138, 190, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.06))
    base = Image.alpha_composite(base, glow)

    # 字
    txt = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    td = ImageDraw.Draw(txt)
    size = int(S * 0.60)
    try:
        font = ImageFont.truetype(FONT_BOLD, size)
    except OSError:
        font = ImageFont.truetype(FONT_SERIF, size)
    ch = "蔚"
    box = td.textbbox((0, 0), ch, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    pos = ((S - tw) / 2 - box[0], (S - th) / 2 - box[1] - S * 0.015)
    # 阴影
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text(pos, ch, font=font, fill=(12, 12, 40, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.012))
    txt = Image.alpha_composite(shadow, txt)
    td = ImageDraw.Draw(txt)
    td.text(pos, ch, font=font, fill=(255, 255, 255, 255), stroke_width=int(S * 0.010), stroke_fill=(255, 255, 255, 255))

    icon = Image.alpha_composite(base, txt)
    icon.putalpha(rounded_mask(S, int(S * 0.22)))

    STATIC.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)

    def save(img, name, size):
        out = img.resize((size, size), Image.LANCZOS)
        out.save(STATIC / name, optimize=True)
        return out

    # favicon.ico：16 / 32 / 48 三档
    ico = icon.resize((256, 256), Image.LANCZOS)
    ico.save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], optimize=True)
    save(icon, "favicon-32.png", 32)
    save(icon, "favicon-16.png", 16)
    save(icon, "apple-touch-icon.png", 180)
    save(icon, "icon-512.png", 512)

    # 预览：大图 + 实际小尺寸并排
    prev = Image.new("RGB", (760, 300), (246, 244, 239))
    big = icon.resize((240, 240), Image.LANCZOS)
    prev.paste(big, (30, 30), big)
    x = 310
    for s in (128, 64, 48, 32, 16):
        small = icon.resize((s, s), Image.LANCZOS)
        prev.paste(small, (x, 30 + (128 - s) // 2), small)
        x += s + 26
    banner = Image.new("RGB", (760, 60), (26, 27, 58))
    bd = ImageDraw.Draw(banner)
    f = ImageFont.truetype(FONT_BOLD, 17)
    b16 = icon.resize((16, 16), Image.LANCZOS)
    b32 = icon.resize((32, 32), Image.LANCZOS)
    banner.paste(b16, (14, 22), b16)
    banner.paste(b32, (40, 14), b32)
    bd.text((84, 18), "蔚来实验室   aiqivy.com", font=f, fill=(240, 238, 246))
    prev.paste(banner, (0, 300 - 60))
    # 注意：banner 覆盖在底部，先贴背景
    out = Image.new("RGB", (760, 360), (246, 244, 239))
    out.paste(prev.crop((0, 0, 760, 300)), (0, 0))
    out.paste(banner, (0, 300))
    out.save(PREVIEW / "favicon-preview.png", optimize=True)

    print("wrote:", ", ".join(sorted(p.name for p in STATIC.glob("favicon*"))))


if __name__ == "__main__":
    build()