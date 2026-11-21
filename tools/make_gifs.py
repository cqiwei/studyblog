"""生成文章配图用的动图（GIF）。

设计约束：
- 纯 Pillow / numpy 绘制，不依赖浏览器截图
- 先在 2 倍尺寸绘制再缩放，边缘才不会锯齿
- 配色与站点主题一致（深底 + 蓝紫青渐变）
- 体积优先：小画幅 + 少调色板 + 紧凑构图

用法：
    python tools/make_gifs.py            # 输出到 content/posts/blog-from-zero/images/
"""

from __future__ import annotations

import math
import os
import time
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 880, 440
S = 2  # 超采样倍数

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "content", "posts", "blog-from-zero", "images",
)

BLUE = (59, 130, 246)
VIOLET = (139, 92, 246)
TEAL = (45, 212, 191)
TEXT = (232, 238, 247)
MUTED = (139, 152, 171)
DIM = (86, 97, 114)

FONT_CN = "C:/Windows/Fonts/msyh.ttc"
FONT_CN_B = "C:/Windows/Fonts/msyhbd.ttc"
FONT_MONO = "C:/Windows/Fonts/consola.ttf"


@lru_cache(maxsize=64)
def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, int(size * S))


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def clamp01(t):
    return max(0.0, min(1.0, t))


def smooth(t):
    t = clamp01(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


_BG_CACHE: dict[str, Image.Image] = {}


def background() -> Image.Image:
    """深色渐变底 + 双色柔光。小尺寸生成后放大，速度快且足够柔和。"""
    if "bg" in _BG_CACHE:
        return _BG_CACHE["bg"].copy()

    fw, fh = W * S, H * S
    sw, sh = max(1, fw // 6), max(1, fh // 6)
    top = np.array([9, 13, 20], dtype=np.float32)
    bottom = np.array([14, 21, 34], dtype=np.float32)
    ramp = np.linspace(0, 1, sh, dtype=np.float32)[:, None, None]
    arr = top[None, None, :] + (bottom - top)[None, None, :] * ramp
    arr = np.repeat(arr, sw, axis=1)
    small = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")

    glow = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse([-sw * 0.3, -sh * 0.55, sw * 0.5, sh * 0.5], fill=BLUE + (56,))
    g.ellipse([sw * 0.58, sh * 0.35, sw * 1.3, sh * 1.3], fill=VIOLET + (44,))
    glow = glow.filter(ImageFilter.GaussianBlur(sh * 0.12))
    small = Image.alpha_composite(small, glow)

    bg = small.resize((fw, fh), Image.BICUBIC)
    _BG_CACHE["bg"] = bg
    return bg.copy()


def panel(img, box, radius=16, fill=(17, 24, 36, 232), outline=(255, 255, 255, 26)):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(box, radius=radius * S, fill=fill, outline=outline, width=max(1, S))


def glow_dot(base: Image.Image, cx, cy, r, color, alpha=255):
    """只在一小块画布上做模糊，避免每帧对整张图做高斯模糊。"""
    R = r * S
    pad = int(R * 4.5) + 2
    tile = Image.new("RGBA", (pad * 2, pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    for k in range(5, 0, -1):
        rr = R * (1 + k * 0.65)
        d.ellipse(
            [pad - rr, pad - rr, pad + rr, pad + rr],
            fill=color + (int(alpha * (0.10 / k)),),
        )
    d.ellipse([pad - R, pad - R, pad + R, pad + R], fill=color + (alpha,))
    tile = tile.filter(ImageFilter.GaussianBlur(max(1.0, R * 0.45)))
    base.alpha_composite(tile, (int(cx * S) - pad, int(cy * S) - pad))


def dashed_line(draw, p1, p2, color, width=2, dash=12, gap=8, offset=0.0):
    """坐标是逻辑坐标，内部统一乘 S。"""
    x1, y1 = p1[0] * S, p1[1] * S
    x2, y2 = p2[0] * S, p2[1] * S
    total = math.hypot(x2 - x1, y2 - y1)
    if total == 0:
        return
    ux, uy = (x2 - x1) / total, (y2 - y1) / total
    dash, gap = dash * S, gap * S
    pos = -offset * S
    while pos < total:
        a = max(0.0, pos)
        b = min(total, pos + dash)
        if b > a:
            draw.line([x1 + ux * a, y1 + uy * a, x1 + ux * b, y1 + uy * b], fill=color, width=width * S)
        pos += dash + gap


def arrow_head(draw, x, y, color=(255, 255, 255, 40), size=6):
    draw.polygon(
        [(x * S, y * S), ((x - size) * S, (y - size * 0.65) * S), ((x - size) * S, (y + size * 0.65) * S)],
        fill=color,
    )


def centered(draw, text, font_, cx, cy, fill):
    box = draw.textbbox((0, 0), text, font=font_)
    w = box[2] - box[0]
    h = box[3] - box[1]
    draw.text((cx * S - w / 2 - box[0], cy * S - h / 2 - box[1]), text, font=font_, fill=fill)


def finish(img: Image.Image) -> Image.Image:
    return img.convert("RGB").resize((W, H), Image.LANCZOS)


def header(d, title, sub):
    d.rounded_rectangle([40 * S, 26 * S, 44 * S, 54 * S], radius=2 * S, fill=BLUE + (230,))
    d.text((54 * S, 26 * S), title, font=font(FONT_CN_B, 21), fill=TEXT)
    d.text((54 * S, 60 * S), sub, font=font(FONT_CN, 12), fill=MUTED)


def caption(d, text, cx, cy, font_size=12, color=(150, 200, 255, 255), pad=18):
    f = font(FONT_CN, font_size)
    tw = d.textlength(text, font=f) / S
    box = [cx * S - (tw / 2 + pad) * S, (cy - 15) * S, cx * S + (tw / 2 + pad) * S, (cy + 15) * S]
    layer = Image.new("RGBA", d._image.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius=15 * S, fill=(19, 29, 43, 240))
    d._image.alpha_composite(layer)
    centered(d, text, f, cx, cy, color)


# --------------------------------------------------------------------------
# 图 1：域名 → DNS → 源站
# --------------------------------------------------------------------------
def gif_dns(frames=40, delay=100):
    nodes = [
        (120, 250, "你的浏览器", "aiqivy.com", BLUE),
        (440, 250, "Cloudflare DNS", "A / AAAA 记录", VIOLET),
        (760, 250, "源站服务器", "203.0.113.10", TEAL),
    ]
    half_w, half_h = 100, 52

    out = []
    for i in range(frames):
        t = i / frames
        img = background()
        d = ImageDraw.Draw(img)
        header(d, "域名是怎么找到服务器的", "DNS 解析链路 · 一次典型的 A 记录查询")

        f_name = font(FONT_CN_B, 16)
        f_sub = font(FONT_CN, 12)

        for k in range(2):
            p1 = (nodes[k][0] + half_w + 10, nodes[k][1])
            p2 = (nodes[k + 1][0] - half_w - 22, nodes[k][1])
            dashed_line(d, p1, p2, (255, 255, 255, 36), width=2, offset=(i * 2.2) % 20)
            arrow_head(d, p2[0] + 8, p2[1], (255, 255, 255, 52))

        # 光点
        if t < 0.66:
            if t < 0.33:
                p = smooth((t - 0.03) / 0.26)
                x = lerp(nodes[0][0] + half_w + 10, nodes[1][0] - half_w - 22, p)
            else:
                p = smooth((t - 0.37) / 0.26)
                x = lerp(nodes[1][0] + half_w + 10, nodes[2][0] - half_w - 22, p)
            glow_dot(img, x, nodes[0][1], 6, (140, 180, 255), 235)

        for idx, (cx, cy, name, sub, accent) in enumerate(nodes):
            lit = 1.0 if idx == 0 else smooth((t - (0.02 + idx * 0.31)) / 0.16)
            box = [cx * S - half_w * S, cy * S - half_h * S, cx * S + half_w * S, cy * S + half_h * S]
            panel(img, box)
            bar = Image.new("RGBA", img.size, (0, 0, 0, 0))
            bd = ImageDraw.Draw(bar)
            bd.rounded_rectangle(
                [box[0] + 15 * S, box[1] + 10 * S, box[2] - 15 * S, box[1] + 13 * S],
                radius=1.5 * S,
                fill=mix(DIM, accent, 0.3 + 0.7 * lit) + (int(90 + 165 * lit),),
            )
            img.alpha_composite(bar)
            centered(d, name, f_name, cx, cy - 11, mix((148, 158, 174), TEXT, lit))
            centered(d, sub, f_sub, cx, cy + 22, mix(DIM, MUTED, lit))

        if t > 0.72:
            a = ease_out((t - 0.72) / 0.16)
            caption(
                d, "A 记录 → 104.21.3.190   ·   源站只放行 Cloudflare 网段",
                440, 388, font_size=12, color=(150, 200, 255, int(255 * a)), pad=22,
            )

        out.append(finish(img))
    save(out, "01-dns.gif", delay)


# --------------------------------------------------------------------------
# 图 2：本地提交 → 推送到 GitHub
# --------------------------------------------------------------------------
def gif_git(frames=40, delay=105):
    hashes = ["29a3274", "966f745", "b794529"]
    out = []
    for i in range(frames):
        t = i / frames
        img = background()
        d = ImageDraw.Draw(img)
        header(d, "从本地仓库到 GitHub", "提交 → 打包 → 推送 · 每一行都是一个可回滚的版本")

        f_name = font(FONT_CN_B, 15)
        f_sub = font(FONT_CN, 11)
        f_mono = font(FONT_MONO, 11)

        panel(img, [52 * S, 118 * S, 390 * S, 300 * S])
        d.text((72 * S, 130 * S), "本地  main", font=f_name, fill=TEXT)
        d.text((72 * S, 154 * S), "3 个提交，尚未推送", font=f_sub, fill=MUTED)
        d.line([72 * S, 236 * S, 370 * S, 236 * S], fill=(255, 255, 255, 26), width=2 * S)

        panel(img, [490 * S, 118 * S, 828 * S, 300 * S], fill=(15, 22, 34, 236))
        d.text((510 * S, 130 * S), "GitHub  origin/main", font=f_name, fill=TEXT)
        d.text((510 * S, 154 * S), "cqiwei/studyblog", font=f_sub, fill=MUTED)
        d.line([510 * S, 236 * S, 808 * S, 236 * S], fill=(255, 255, 255, 22), width=2 * S)

        for k in range(3):
            appear = clamp01((t - 0.05 - k * 0.09) / 0.13)
            if appear <= 0:
                continue
            cx = 116 + k * 88
            glow_dot(img, cx, 236, 6.5 * appear, mix(BLUE, TEAL, k / 2), int(235 * appear))
            centered(d, hashes[k], f_mono, cx, 264, mix(DIM, MUTED, appear))

        for k in range(3):
            start = 0.32 + k * 0.10
            p = clamp01((t - start) / 0.18)
            if p <= 0:
                continue
            px = lerp(116 + k * 88, 548 + k * 88, ease_out(p))
            py = 236 - math.sin(p * math.pi) * 46
            glow_dot(img, px, py, 6.5, mix(BLUE, VIOLET, k / 2), 230)
            if p >= 1:
                glow_dot(img, 548 + k * 88, 236, 6.5, mix(BLUE, TEAL, k / 2), 235)
                centered(d, hashes[k], f_mono, 548 + k * 88, 264, MUTED)

        if t > 0.68:
            a = ease_out((t - 0.68) / 0.14)
            caption(d, "git push origin main", 440, 372, font_size=13,
                    color=(150, 200, 255, int(255 * a)), pad=24)

        out.append(finish(img))
    save(out, "02-git.gif", delay)


# --------------------------------------------------------------------------
# 图 3：终端里的部署
# --------------------------------------------------------------------------
def gif_deploy(frames=56, delay=115):
    lines = [
        ("cmd", "hugo --minify --gc"),
        ("ok", "Total in 830 ms"),
        ("cmd", "./deploy/scripts/deploy.ps1"),
        ("log", "==> packing release 20261121-115732"),
        ("log", "==> uploading to root@203.0.113.10"),
        ("log", "==> activating"),
        ("ok", "OK  release is live"),
    ]
    schedule = []
    t0 = 0.03
    for kind, text in lines:
        dur = 0.028 + len(text) * 0.0016
        schedule.append((t0, t0 + dur, kind, text))
        t0 += dur + 0.022

    out = []
    for i in range(frames):
        t = i / frames
        img = background()
        d = ImageDraw.Draw(img)
        header(d, "一条命令上线", "构建 → 打包 → 上传 → 切换软链接 → 重载 nginx")

        f_mono = font(FONT_MONO, 14)
        f_mono_s = font(FONT_MONO, 11)

        box = [78 * S, 96 * S, 802 * S, 340 * S]
        panel(img, box, radius=14, fill=(12, 17, 26, 246))
        d = ImageDraw.Draw(img)
        d.line([78 * S, 132 * S, 802 * S, 132 * S], fill=(255, 255, 255, 22), width=2 * S)
        for k, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
            x0 = 96 + k * 18
            d.ellipse([x0 * S, 110 * S, (x0 + 8) * S, 118 * S], fill=c)
        d.text((186 * S, 107 * S), "deploy  —  zsh", font=f_mono_s, fill=MUTED)

        y = 146
        for start, end, kind, text in schedule:
            if t < start:
                break
            shown = text[: int(len(text) * clamp01((t - start) / (end - start)))]
            color = {"cmd": (170, 200, 255), "ok": (110, 231, 183), "log": MUTED}[kind]
            prefix = "$ " if kind == "cmd" else "  "
            d.text((100 * S, y * S), prefix + shown, font=f_mono, fill=color)
            if t < end:
                tw = d.textlength(prefix + shown, font=f_mono)
                if (i // 3) % 2 == 0:
                    d.rectangle(
                        [100 * S + tw + 2 * S, y * S + 2 * S, 100 * S + tw + 9 * S, y * S + 15 * S],
                        fill=(150, 200, 255),
                    )
            y += 28

        last = schedule[-1]
        if t > last[1] - 0.01:
            p = ease_out((t - last[1]) / 0.10)
            r = 10 * p
            if r > 1:
                glow_dot(img, 440, 386, r, TEAL, 230)
            if p > 0.45:
                a = int(255 * (p - 0.45) / 0.55)
                centered(d, "线上已更新 · 刷新即见", font(FONT_CN, 13), 440, 386, (110, 231, 183, a))

        out.append(finish(img))
    save(out, "03-deploy.gif", delay)


@lru_cache(maxsize=1)
def palette_image() -> Image.Image:
    """固定调色板：背景渐变采样 + 主题色。

    GIF 只有 256 色，用逐帧自适应调色板时，几个像素的小色块（终端红绿灯）
    会被挤掉、退化成灰色；固定调色板能保证关键颜色一定在表里，而且所有帧
    共用一张表，文件更小。
    """
    bg = background().convert("RGB")
    cols: list[tuple[int, int, int]] = []

    # 背景渐变两侧各采样 96 个点，保证没有明显色带
    for xf, n in ((0.22, 96), (0.72, 96)):
        x = int(bg.width * xf)
        for i in range(n):
            y = int((i + 0.5) * bg.height / n)
            cols.append(bg.getpixel((x, y)))

    keys = [
        (255, 95, 87), (254, 188, 46), (40, 200, 64),      # 终端红绿灯
        (59, 130, 246), (139, 92, 246), (45, 212, 191),    # 主题蓝紫青
        (232, 238, 247), (190, 199, 214), (139, 152, 171), (86, 97, 114),
        (12, 17, 26), (17, 24, 36), (15, 22, 34), (19, 29, 43), (20, 30, 44),
        (170, 200, 255), (150, 200, 255), (110, 231, 183), (148, 158, 174),
        (255, 255, 255),
    ]
    cols.extend(keys)

    for c in [(59, 130, 246), (139, 92, 246), (45, 212, 191), (232, 238, 247)]:
        for t in (0.2, 0.4, 0.6, 0.8):
            cols.append(mix((12, 17, 26), c, t))

    cols = cols[:256]
    while len(cols) < 256:
        cols.append((0, 0, 0))

    flat: list[int] = []
    for c in cols:
        flat.extend(c)
    p = Image.new("P", (1, 1))
    p.putpalette(flat)
    return p


def save(frames, name, delay):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    pal = [f.quantize(palette=palette_image(), dither=Image.NONE) for f in frames]
    pal[0].save(
        path,
        save_all=True,
        append_images=pal[1:],
        duration=delay,
        loop=0,
        optimize=True,
        disposal=1,
    )
    size = os.path.getsize(path) / 1024
    print(f"{name:16} {len(frames):3d} frames  {size:7.1f} KB")

    preview_dir = os.path.join(os.path.dirname(OUT_DIR), "..", "..", ".deploy", "previews")
    os.makedirs(preview_dir, exist_ok=True)
    frames[len(frames) // 2].save(os.path.join(preview_dir, name.replace(".gif", ".png")))


if __name__ == "__main__":
    gif_dns()
    gif_git()
    gif_deploy()
