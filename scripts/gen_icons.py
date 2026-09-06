"""
Generates placeholder app icons for the PWA manifest and Next.js icon
file conventions. Intentionally simple: a calm, muted background with a
"connection" glyph (two nodes + a line), matching the R&D doc's
non-clinical, non-alarm tone. This is a placeholder pending real
branding (see R&D doc Section 29 name candidates) — swap freely.
"""
from PIL import Image, ImageDraw

BG = (63, 110, 99, 255)      # muted teal, matches manifest theme_color
NODE = (250, 248, 245, 255)  # warm off-white, matches manifest background_color


def draw_connection_glyph(draw: ImageDraw.ImageDraw, size: int, maskable: bool):
    # Maskable icons need extra safe-area padding (~10% each side) since
    # OS launchers may crop to a circle/squircle.
    pad = size * (0.24 if maskable else 0.14)
    node_r = size * 0.085
    x1, y1 = pad + node_r, size - pad - node_r
    x2, y2 = size - pad - node_r, pad + node_r

    draw.line([(x1, y1), (x2, y2)], fill=NODE, width=max(2, int(size * 0.045)))
    draw.ellipse([x1 - node_r, y1 - node_r, x1 + node_r, y1 + node_r], fill=NODE)
    draw.ellipse([x2 - node_r, y2 - node_r, x2 + node_r, y2 + node_r], fill=NODE)


def make_icon(path: str, size: int, maskable: bool = False, rounded: bool = True):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if maskable:
        # Maskable icons should fill edge-to-edge with no transparency —
        # the OS applies its own mask shape on top.
        draw.rectangle([0, 0, size, size], fill=BG)
    elif rounded:
        radius = int(size * 0.22)
        draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=BG)
    else:
        draw.rectangle([0, 0, size, size], fill=BG)

    draw_connection_glyph(draw, size, maskable)
    img.save(path)
    print(f"wrote {path} ({size}x{size}, maskable={maskable})")


if __name__ == "__main__":
    import os

    fe = "/home/claude/campus-connect/frontend"
    os.makedirs(f"{fe}/public/icons", exist_ok=True)

    # Manifest icons (public/, static paths referenced literally in manifest.ts)
    make_icon(f"{fe}/public/icons/icon-192.png", 192)
    make_icon(f"{fe}/public/icons/icon-512.png", 512)
    make_icon(f"{fe}/public/icons/icon-maskable-512.png", 512, maskable=True)

    # Next.js file-convention icons (auto <link> tag injection)
    make_icon(f"{fe}/src/app/icon.png", 512)
    make_icon(f"{fe}/src/app/apple-icon.png", 180, rounded=False)
