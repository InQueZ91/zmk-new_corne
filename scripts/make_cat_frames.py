#!/usr/bin/env python3
"""Builds the five typing-pose frames from the hand-drawn pixel art in cat/base.png
and writes them as LVGL images to src/dongle_screen/cat_frames.c (generated, committed).

cat/base.png is the "both hands down" pose (160x84, transparent background). The other
poses are derived from it by moving the hands and closing the eyes:

    cat_both    base picture, both hands down
    cat_left    left hand down, right hand lifted     (key on the left half)
    cat_right   right hand down, left hand lifted     (key on the right half)
    cat_idle    both hands lifted, waiting
    cat_sleep   hands down, eyes closed, floating "z"

LVGL 8 LV_IMG_CF_INDEXED_4BIT: 16-colour palette, so the art is reduced to 15 colours
(+ the screen background). Needs Pillow (build-time only; the firmware needs nothing).

    python scripts/make_cat_frames.py [--preview out.png]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (0x10, 0x12, 0x19)          # COLOR_BG of the screen
LIFT = 5                         # pixels a lifted hand moves up
HAND_TOP = 69                    # rows from here down belong to the hands / forearms
SPLIT = 80                       # x < SPLIT is the left half of the picture
EYES = ((63, 73), (84, 94))      # x ranges of the two eyes
EYE_ROWS = (46, 47, 48)   # shade, shade, closed-lid line


def load():
    im = Image.open(os.path.join(ROOT, "cat", "base.png")).convert("RGBA")
    w, h = im.size
    if (w, h) != (160, 84):
        sys.exit("cat/base.png must be 160x84, got %dx%d" % (w, h))
    pix = [[im.getpixel((x, y)) for x in range(w)] for y in range(h)]
    count = {}
    for row in pix:
        for p in row:
            if p[3] >= 128:
                count[p[:3]] = count.get(p[:3], 0) + 1
    # Reduce to 15 colours: fold the rarest colour into its nearest neighbour.
    mapping = {c: c for c in count}
    live = dict(count)
    while len(live) > 15:
        rare = min(live, key=live.get)
        near = min((c for c in live if c != rare),
                   key=lambda c: sum((a - b) ** 2 for a, b in zip(c, rare)))
        live[near] += live.pop(rare)
        for k, v in mapping.items():
            if v == rare:
                mapping[k] = near
    palette = [BG] + sorted(live, key=live.get, reverse=True)
    index = {c: i for i, c in enumerate(palette)}
    img = [[0 if p[3] < 128 else index[mapping[p[:3]]] for p in row] for row in pix]
    return img, palette


def nearest(palette, rgb):
    return min(range(1, len(palette)),
               key=lambda i: sum((a - b) ** 2 for a, b in zip(palette[i], rgb)))


def lift(img, x0, x1, dark):
    """Move the hand rows of columns x0..x1 up by LIFT; the gap at the bottom stays dark."""
    out = [row[:] for row in img]
    h = len(img)
    for x in range(x0, x1):
        for y in range(HAND_TOP, h):
            out[y - LIFT][x] = img[y][x]
        for y in range(h - LIFT, h):
            out[y][x] = dark
    return out


def close_eyes(img, skin, lid, shade):
    out = [row[:] for row in img]
    for x0, x1 in EYES:
        for x in range(x0, x1 + 1):
            out[EYE_ROWS[0]][x] = shade
            out[EYE_ROWS[1]][x] = shade
            out[EYE_ROWS[2]][x] = lid
    return out


Z_BIG = ("#####", "...#.", "..#..", ".#...", "#####")
Z_SMALL = ("###", ".#.", "###")


def stamp(img, x, y, glyph, colour):
    for dy, row in enumerate(glyph):
        for dx, ch in enumerate(row):
            if ch == "#":
                img[y + dy][x + dx] = colour


def frames():
    base, pal = load()
    dark = nearest(pal, (6, 6, 8))
    skin = nearest(pal, (199, 176, 139))
    shade = nearest(pal, (90, 78, 68))
    light = nearest(pal, (228, 210, 170))
    left_up = lift(base, 0, SPLIT, dark)
    right_up = lift(base, SPLIT, 160, dark)
    both_up = lift(left_up, SPLIT, 160, dark)
    sleep = close_eyes(base, skin, dark, shade)
    stamp(sleep, 140, 22, Z_BIG, light)
    stamp(sleep, 130, 12, Z_SMALL, light)
    return pal, [
        ("cat_idle", both_up),
        ("cat_left", right_up),     # left hand stays down, right hand lifted
        ("cat_right", left_up),
        ("cat_both", base),
        ("cat_sleep", sleep),
    ]


def c_image(name, img, pal):
    h, w = len(img), len(img[0])
    data = bytearray()
    for i in range(16):                                      # lv_color32_t: B, G, R, A
        r, g, b = pal[i] if i < len(pal) else (0, 0, 0)
        data += bytes((b, g, r, 0xFF))
    for row in img:
        for x in range(0, w, 2):
            data.append((row[x] << 4) | row[x + 1])          # first pixel in high nibble
    lines = ["    " + ", ".join("0x%02x" % b for b in data[i:i + 16]) + ","
             for i in range(0, len(data), 16)]
    return (
        "static const uint8_t %s_map[] = {\n%s\n};\n\n"
        "const lv_img_dsc_t %s = {\n"
        "    .header.cf = LV_IMG_CF_INDEXED_4BIT,\n"
        "    .header.always_zero = 0,\n"
        "    .header.w = %d,\n"
        "    .header.h = %d,\n"
        "    .data_size = sizeof(%s_map),\n"
        "    .data = %s_map,\n"
        "};\n" % (name, "\n".join(lines), name, w, h, name, name)
    )


def main():
    pal, fr = frames()
    out = os.path.join(ROOT, "src", "dongle_screen", "cat_frames.c")
    parts = ["/*\n * GENERATED by scripts/make_cat_frames.py from cat/base.png - do not edit by hand.\n"
             " * 160x84, LV_IMG_CF_INDEXED_4BIT.\n */\n#include <lvgl.h>\n"]
    parts += [c_image(n, img, pal) for n, img in fr]
    with open(out, "w", newline="\n") as f:
        f.write("\n".join(parts))
    print("wrote", out)
    if "--preview" in sys.argv:
        path = sys.argv[sys.argv.index("--preview") + 1]
        sheet = Image.new("RGB", (164 * 5, 84 * 2 + 4), (255, 255, 255))
        for i, (_, img) in enumerate(fr):
            im = Image.new("RGB", (160, 84))
            im.putdata([pal[c] for row in img for c in row])
            sheet.paste(im, (i * 164, 0))
        sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST)
        sheet.save(path)
        print("preview:", path)


if __name__ == "__main__":
    main()
