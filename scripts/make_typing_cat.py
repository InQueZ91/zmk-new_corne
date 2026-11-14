#!/usr/bin/env python3
"""Draws the ORIGINAL typing cat for the dongle screen and writes it as LVGL images.

Output: src/dongle_screen/cat_frames.c (generated, committed). Five 160x84 frames,
LVGL 8 LV_IMG_CF_INDEXED_4BIT (16-colour palette + 4 bits per pixel, ~6.8 KB each):

    cat_idle    paws up, waiting
    cat_left    left paw down   (key on the left half)
    cat_right   right paw down  (key on the right half)
    cat_both    both paws down
    cat_sleep   eyes closed, paws resting (no typing for a while)

Pure standard library. Usage:
    python scripts/make_typing_cat.py [--preview out.png]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_cat_gif import blank, ellipse, line, px, tri, write_png  # noqa: E402

W, H = 80, 42   # drawn at 80x42, stored at 2x (160x84)
SCALE = 2

PAL = [
    (16, 18, 25),      # 0 background (matches COLOR_BG 0x101219)
    (232, 150, 70),    # 1 orange fur
    (190, 105, 40),    # 2 darker stripe
    (250, 240, 225),   # 3 cream (muzzle, chest, paws)
    (240, 140, 150),   # 4 pink
    (110, 210, 120),   # 5 eye green
    (15, 12, 12),      # 6 pupil / mouth
    (110, 60, 25),     # 7 outline
    (200, 205, 215),   # 8 whiskers / zzz
    (34, 38, 52),      # 9 desk
    (58, 64, 84),      # 10 keyboard body
    (96, 104, 128),    # 11 keycaps
    (77, 163, 255),    # 12 key flash (blue, matches COLOR_BLE)
    (0, 0, 0), (0, 0, 0), (0, 0, 0),
]

UP_L, UP_R = (22, 24), (58, 24)          # raised paws
DOWN_L, DOWN_R = (29, 34), (51, 34)      # paws on the keyboard
SHOULDER_L, SHOULDER_R = (31, 28), (49, 28)


def keyboard(img, flash_l, flash_r):
    for y in range(37, H):                                   # desk
        for x in range(W):
            px(img, x, y, 9)
    for y in range(32, 39):                                  # keyboard body
        for x in range(16, 64):
            px(img, x, y, 10)
    for row, y in enumerate((33, 35)):                       # keycaps
        for x in range(18 + row, 62, 4):
            c = 11
            if flash_l and row == 0 and 18 <= x <= 22:       # keys beside the paw light up
                c = 12
            if flash_r and row == 0 and 54 <= x <= 58:
                c = 12
            line(img, (x, y), (x + 2, y), c)


def arm(img, shoulder, paw, beans):
    line(img, shoulder, paw, 7, thick=4)
    line(img, (shoulder[0] + 1, shoulder[1] + 1), (paw[0] + 1, paw[1] + 1), 1, thick=2)
    ellipse(img, paw[0] + 1, paw[1] + 1, 3.6, 2.6, 7)
    ellipse(img, paw[0] + 1, paw[1] + 1, 2.8, 1.8, 3)
    if beans:                                                # toe beans on raised paws
        for dx in (-1, 1, 3):
            px(img, paw[0] + dx, paw[1], 4)


def head(img, eyes):
    for sx in (-1, 1):                                       # ears
        base = 40 + sx * 8
        tri(img, (base - sx * 4, 10), (base + sx * 1, 1), (base + sx * 6, 9), 7)
        tri(img, (base - sx * 3, 9), (base + sx * 1, 3), (base + sx * 5, 8), 1)
        tri(img, (base - sx * 1, 8), (base + sx * 1, 5), (base + sx * 3, 8), 4)
    ellipse(img, 40, 16, 13, 10, 7)
    ellipse(img, 40, 16, 12, 9, 1)
    for x in (37, 40, 43):                                   # forehead stripes
        line(img, (x, 8), (x, 10), 2)
    ellipse(img, 40, 20, 5.5, 3.6, 3)                        # muzzle

    for sx in (-1, 1):
        ex = 40 + sx * 6
        if eyes == "closed":                                 # sleepy arcs
            px(img, ex - 2, 15, 6)
            line(img, (ex - 1, 16), (ex + 1, 16), 6)
            px(img, ex + 2, 15, 6)
        else:
            look = 1 if eyes == "down" else 0                # looking at the keys
            ellipse(img, ex, 15, 2.6, 2.6, 6)
            ellipse(img, ex, 15, 2.0, 2.0, 5)
            ellipse(img, ex, 15 + look, 0.9, 1.4, 6)
            px(img, ex - 1, 14, 3)                           # glint

    tri(img, (39, 18), (41, 18), (40, 19), 4)                # nose
    px(img, 40, 20, 6)
    px(img, 39, 21, 6)
    px(img, 41, 21, 6)
    for sx in (-1, 1):                                       # whiskers
        for dy in (-1, 1):
            line(img, (40 + sx * 7, 19 + dy), (40 + sx * 14, 18 + dy * 2), 8)


def zzz(img):
    for (x, y, s) in ((58, 8, 3), (64, 3, 4)):
        line(img, (x, y), (x + s, y), 8)
        line(img, (x + s, y), (x, y + s), 8)
        line(img, (x, y + s), (x + s, y + s), 8)


def cat(left_down, right_down, sleeping=False):
    img = blank()
    ellipse(img, 40, 30, 14, 9, 7)                           # body (behind the keyboard)
    ellipse(img, 40, 30, 13, 8, 1)
    ellipse(img, 40, 31, 6, 6, 3)                            # chest
    keyboard(img, left_down and not sleeping, right_down and not sleeping)
    head(img, "closed" if sleeping else ("down" if (left_down or right_down) else "open"))
    arm(img, SHOULDER_L, DOWN_L if left_down else UP_L, beans=not left_down)
    arm(img, SHOULDER_R, DOWN_R if right_down else UP_R, beans=not right_down)
    if sleeping:
        zzz(img)
    return img


FRAMES = [
    ("cat_idle", cat(False, False)),
    ("cat_left", cat(True, False)),
    ("cat_right", cat(False, True)),
    ("cat_both", cat(True, True)),
    ("cat_sleep", cat(True, True, sleeping=True)),
]


def scaled(img):
    rows = []
    for row in img:
        wide = [c for c in row for _ in range(SCALE)]
        rows.extend([wide] * SCALE)
    return rows


def c_image(name, img):
    rows = scaled(img)
    w, h = len(rows[0]), len(rows)
    data = bytearray()
    for r, g, b in PAL:                                      # lv_color32_t: B, G, R, A
        data += bytes((b, g, r, 0xFF))
    for row in rows:
        for x in range(0, w, 2):
            data.append((row[x] << 4) | row[x + 1])          # first pixel in high nibble
    lines = []
    for i in range(0, len(data), 16):
        lines.append("    " + ", ".join("0x%02x" % b for b in data[i:i + 16]) + ",")
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
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "src", "dongle_screen", "cat_frames.c")
    parts = [
        "/*\n * GENERATED by scripts/make_typing_cat.py - do not edit by hand.\n"
        " * Original typing cat, 160x84, LV_IMG_CF_INDEXED_4BIT.\n */\n"
        "#include <lvgl.h>\n"
    ]
    for name, img in FRAMES:
        parts.append(c_image(name, img))
    with open(out, "w", newline="\n") as f:
        f.write("\n".join(parts))
    print("wrote", out)

    if "--preview" in sys.argv:
        path = sys.argv[sys.argv.index("--preview") + 1]
        sheet = []
        frames = [scaled(img) for _, img in FRAMES]
        for y in range(H * SCALE):
            row = []
            for fr in frames:
                for c in fr[y]:
                    row.extend(PAL[c])
                row.extend((255, 255, 255) * 4)              # white gap between frames
            sheet.append(row)
        write_png(path, (W * SCALE + 4) * len(frames), H * SCALE, sheet)
        print("preview:", path)


if __name__ == "__main__":
    main()
