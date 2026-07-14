"""Generate the LatAm Data MCP logo (app-icon style).

Rounded square with a teal->emerald gradient, a white location pin
(Latin America / geo) and a green check inside it (validation — the
core of the product). Rendered at 4x and downscaled for smooth edges.
"""

from PIL import Image, ImageDraw

S = 512          # final size
SS = 4           # supersample factor
N = S * SS

# --- palette ---------------------------------------------------------------
TOP = (13, 148, 136)     # teal-600  #0D9488
BOT = (5, 150, 105)      # emerald-600 #059669
WHITE = (255, 255, 255)
CHECK = (5, 150, 105)    # emerald for the check


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_mask(size, radius):
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    return m


# --- background: vertical gradient -----------------------------------------
bg = Image.new("RGB", (N, N))
px = bg.load()
for y in range(N):
    c = lerp(TOP, BOT, y / (N - 1))
    for x in range(N):
        px[x, y] = c

# --- foreground layer (pin + check) ----------------------------------------
fg = Image.new("RGBA", (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(fg)

cx = N // 2
pin_top = int(N * 0.20)
pin_r = int(N * 0.185)          # radius of the pin's circular head
head_cy = pin_top + pin_r
tip_y = int(N * 0.80)

# pin head (circle)
d.ellipse([cx - pin_r, head_cy - pin_r, cx + pin_r, head_cy + pin_r], fill=WHITE)
# pin tail (triangle from circle sides down to the tip)
import math
theta = math.radians(52)
lx = cx - int(pin_r * math.sin(theta))
rx = cx + int(pin_r * math.sin(theta))
ty = head_cy + int(pin_r * math.cos(theta))
d.polygon([(lx, ty), (rx, ty), (cx, tip_y)], fill=WHITE)

# inner check inside the head
cw = int(pin_r * 0.42)          # stroke width
p1 = (cx - int(pin_r * 0.55), head_cy + int(pin_r * 0.02))
p2 = (cx - int(pin_r * 0.12), head_cy + int(pin_r * 0.42))
p3 = (cx + int(pin_r * 0.60), head_cy - int(pin_r * 0.42))
d.line([p1, p2, p3], fill=CHECK, width=cw, joint="curve")
# round the check end-caps
for p in (p1, p2, p3):
    d.ellipse([p[0] - cw // 2, p[1] - cw // 2, p[0] + cw // 2, p[1] + cw // 2], fill=CHECK)

# --- compose ---------------------------------------------------------------
bg.paste(fg, (0, 0), fg)
mask = rounded_mask(N, radius=int(N * 0.22))
icon = Image.new("RGBA", (N, N), (0, 0, 0, 0))
icon.paste(bg, (0, 0), mask)

# --- export at multiple sizes ----------------------------------------------
for out_size, name in [(512, "logo.png"), (400, "logo-400.png"), (256, "logo-256.png")]:
    icon.resize((out_size, out_size), Image.LANCZOS).save(f"assets/{name}")
    print("wrote assets/" + name)
