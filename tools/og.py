"""Share images (1200x630) for WhatsApp, Facebook, etc. Called by build.py.
Fonts: DejaVu Serif (tools/fonts, free licence, has Greek). Needs Pillow (installed by the GitHub workflow).
The images are deterministic: rebuilding them gives the same bytes, so git sees no change."""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BLUE = (26, 86, 180)
INK = (28, 31, 36)
MUTED = (96, 104, 116)
BG = (255, 255, 255)
SOFT = (238, 243, 251)
HERE = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(HERE, "fonts", "DejaVuSerif.ttf")
FB = os.path.join(HERE, "fonts", "DejaVuSerif-Bold.ttf")
_cache = {}


def font(path, size):
    k = (path, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(path, size)
    return _cache[k]


def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, path, maxw, maxlines, start, minsize):
    size = start
    while size >= minsize:
        f = font(path, size)
        lines = wrap(draw, text, f, maxw)
        if len(lines) <= maxlines:
            return f, lines
        size -= 4
    f = font(path, minsize)
    lines = wrap(draw, text, f, maxw)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        lines[-1] = lines[-1].rstrip(" ,.;:") + "…"
    return f, lines


def frame(footer):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, H - 96, W, H], fill=SOFT)
    d.rectangle([0, 0, 16, H], fill=BLUE)
    x, y, s = 80, 64, 84  # logo: blue rounded square with a white mu, then "Masimera"
    d.rounded_rectangle([x, y, x + s, y + s], radius=20, fill=BLUE)
    fm = font(FR, 64)
    bb = d.textbbox((0, 0), "μ", font=fm)
    d.text((x + (s - (bb[2] - bb[0])) / 2 - bb[0], y + (s - (bb[3] - bb[1])) / 2 - bb[1]), "μ", font=fm, fill="white")
    d.text((x + s + 22, y + 14), "Masimera", font=font(FB, 46), fill=INK)
    d.text((80, H - 70), footer, font=font(FR, 30), fill=BLUE)
    return im, d


def save(im, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, optimize=True)


def lesson_image(title, subtitle, footer, out):
    """Lesson / quiz: the title of the day in big letters, the English title below."""
    im, d = frame(footer)
    f, lines = fit(d, title, FB, W - 180, 3, 76, 48)
    y = 210
    for ln in lines:
        d.text((80, y), ln, font=f, fill=INK)
        y += int(f.size * 1.22)
    if subtitle:
        fs, sub = fit(d, subtitle, FR, W - 180, 2, 38, 30)
        y += 14
        for ln in sub:
            d.text((80, y), ln, font=fs, fill=MUTED)
            y += int(fs.size * 1.3)
    save(im, out)


def challenge_image(banner, title, subtitle, footer, out):
    """Quiz challenge sent to a friend: a big blue banner (« A friend challenges your Greek! »), then the lesson title."""
    im, d = frame(footer)
    fb, bl = fit(d, banner, FB, W - 220, 1, 64, 40)
    bw = d.textlength(bl[0], font=fb)
    d.rounded_rectangle([80, 190, 80 + bw + 60, 190 + fb.size + 44], radius=24, fill=BLUE)
    d.text((110, 190 + 18), bl[0], font=fb, fill="white")
    y = 190 + fb.size + 44 + 40
    f, lines = fit(d, title, FB, W - 180, 2, 52, 36)
    for ln in lines:
        d.text((80, y), ln, font=f, fill=INK)
        y += int(f.size * 1.22)
    if subtitle:
        fs, sub = fit(d, subtitle, FR, W - 180, 1, 32, 26)
        d.text((80, y + 6), sub[0], font=fs, fill=MUTED)
    save(im, out)


def page_image(big, native, tagline, footer, out):
    """Fixed pages (home, /gr/, /it/): small line in blue, big title, short description."""
    im, d = frame(footer)
    d.text((80, 200), native, font=font(FR, 40), fill=BLUE)
    d.text((80, 256), big, font=font(FB, 84), fill=INK)
    fs, sub = fit(d, tagline, FR, W - 180, 3, 32, 26)
    y = 372
    for ln in sub:
        d.text((80, y), ln, font=fs, fill=MUTED)
        y += int(fs.size * 1.35)
    save(im, out)
