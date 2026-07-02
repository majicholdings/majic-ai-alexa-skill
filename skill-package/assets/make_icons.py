"""Generate public-safe placeholder icons for the Majic AI Alexa skill.

Produces the two PNG sizes the Alexa Developer Console requires:
  * en-US_smallIcon.png  -> 108x108
  * en-US_largeIcon.png  -> 512x512

Dark/blue tech style with a "MAJIC AI" wordmark and an "M" monogram. Uses only
Pillow and bundled fonts, so it is fully reproducible and contains no
copyrighted Amazon/Alexa artwork. Re-run with:  python3 make_icons.py
"""

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = "images"

# Dark navy -> electric blue vertical gradient with a rounded-square mask.
TOP = (11, 18, 38)        # deep navy
BOTTOM = (28, 72, 168)    # electric blue
ACCENT = (94, 205, 255)   # cyan glow
TEXT = (240, 248, 255)    # near-white


def _load_font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(size):
    img = Image.new("RGB", (size, size), TOP)
    px = img.load()
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(TOP[0] + (BOTTOM[0] - TOP[0]) * t)
        g = int(TOP[1] + (BOTTOM[1] - TOP[1]) * t)
        b = int(TOP[2] + (BOTTOM[2] - TOP[2]) * t)
        for x in range(size):
            px[x, y] = (r, g, b)
    return img


def _rounded_mask(size, radius):
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return mask


def _centered(draw, text, font, cx, y):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (r - l) / 2 - l, y), text, font=font, fill=TEXT)
    return b - t


def build(size):
    img = _gradient(size).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Accent ring framing the monogram.
    pad = int(size * 0.16)
    ring_w = max(2, int(size * 0.02))
    draw.ellipse(
        [pad, pad, size - pad, size - pad],
        outline=ACCENT + (255,),
        width=ring_w,
    )

    # "M" monogram, centered high.
    mono_font = _load_font(int(size * 0.42))
    _centered(draw, "M", mono_font, size / 2, int(size * 0.20))

    # "MAJIC AI" wordmark near the bottom (large icon only; too small at 108).
    if size >= 256:
        word_font = _load_font(int(size * 0.11))
        _centered(draw, "MAJIC AI", word_font, size / 2, int(size * 0.72))

    # Apply rounded-square mask so corners are clean on the console.
    radius = int(size * 0.18)
    mask = _rounded_mask(size, radius)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def main():
    build(108).save(f"{OUT_DIR}/en-US_smallIcon.png")
    build(512).save(f"{OUT_DIR}/en-US_largeIcon.png")
    print("wrote", f"{OUT_DIR}/en-US_smallIcon.png", "and",
          f"{OUT_DIR}/en-US_largeIcon.png")


if __name__ == "__main__":
    main()
