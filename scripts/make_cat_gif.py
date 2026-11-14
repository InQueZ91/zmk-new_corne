#!/usr/bin/env python3
"""Draws a small ORIGINAL animated cat and writes it as gifs/cat.gif (160x84).

Pure standard library (own GIF encoder), so nothing needs to be installed.
Usage:  python scripts/make_cat_gif.py [out.gif] [--check]
  --check  decodes the written GIF again, compares it with the source frames
           and writes <out>.preview.png (contact sheet).
"""
import math
import struct
import sys
import zlib

W, H = 80, 42          # drawn at 80x42, written at 2x (160x84)
SCALE = 2
FRAMES = 12
DELAY_CS = 12          # 1/100 s per frame

# 16-colour palette (GIF needs a power of two)
PAL = [
    (18, 20, 30),      # 0 background
    (232, 150, 70),    # 1 orange fur
    (190, 105, 40),    # 2 darker stripe
    (250, 240, 225),   # 3 cream (muzzle, chest, paws)
    (240, 140, 150),   # 4 pink
    (110, 210, 120),   # 5 eye green
    (15, 12, 12),      # 6 pupil / mouth
    (110, 60, 25),     # 7 outline
    (200, 205, 215),   # 8 whiskers
    (34, 38, 52),      # 9 floor shadow
    (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0), (0, 0, 0),
]


def blank():
    return [[0] * W for _ in range(H)]


def px(img, x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img[y][x] = c


def ellipse(img, cx, cy, rx, ry, c):
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                px(img, x, y, c)


def tri(img, a, b, c_, col):
    xs = [a[0], b[0], c_[0]]
    ys = [a[1], b[1], c_[1]]
    for y in range(min(ys), max(ys) + 1):
        for x in range(min(xs), max(xs) + 1):
            d1 = (x - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (y - b[1])
            d2 = (x - c_[0]) * (b[1] - c_[1]) - (b[0] - c_[0]) * (y - c_[1])
            d3 = (x - a[0]) * (c_[1] - a[1]) - (c_[0] - a[0]) * (y - a[1])
            neg = d1 < 0 or d2 < 0 or d3 < 0
            pos = d1 > 0 or d2 > 0 or d3 > 0
            if not (neg and pos):
                px(img, x, y, col)


def line(img, p0, p1, c, thick=1):
    n = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]), 1)
    for i in range(n + 1):
        x = round(p0[0] + (p1[0] - p0[0]) * i / n)
        y = round(p0[1] + (p1[1] - p0[1]) * i / n)
        for dx in range(thick):
            for dy in range(thick):
                px(img, x + dx, y + dy, c)


def tail(img, t):
    sway = math.sin(2 * math.pi * t)
    p0, p1 = (50, 37), (64, 38)
    p2 = (61 + 5 * sway, 20 + 2 * math.cos(2 * math.pi * t))
    pts = []
    for i in range(0, 21):
        u = i / 20
        x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0]
        y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]
        pts.append((round(x), round(y)))
    for i, (x, y) in enumerate(pts):
        r = 2 if i < 17 else 1
        ellipse(img, x, y, r + 0.6, r + 0.6, 7)
    for i, (x, y) in enumerate(pts):
        r = 2 if i < 17 else 1
        ellipse(img, x, y, r, r, 2 if i % 5 in (3, 4) else 1)


def cat(frame):
    t = frame / FRAMES
    img = blank()
    ellipse(img, 40, 40, 20, 2.2, 9)                       # floor shadow
    tail(img, t)
    ellipse(img, 40, 31, 12.5, 10.5, 7)                    # body outline
    ellipse(img, 40, 31, 11.5, 9.5, 1)
    ellipse(img, 40, 33, 5.5, 7.5, 3)                      # chest
    for x in (33, 47):                                     # side stripes
        line(img, (x - 1, 27), (x + 1, 28), 2)
        line(img, (x - 1, 31), (x + 1, 32), 2)
    ellipse(img, 35, 39, 3.6, 2.2, 7)                      # paws
    ellipse(img, 45, 39, 3.6, 2.2, 7)
    ellipse(img, 35, 39, 2.8, 1.5, 3)
    ellipse(img, 45, 39, 2.8, 1.5, 3)

    twitch = 1 if frame in (4, 5) else 0                   # left ear twitch
    for sx in (-1, 1):                                     # ears
        base = 40 + sx * 8
        dy = twitch if sx == -1 else 0
        tri(img, (base - sx * 4, 10), (base + sx * 1, 1 + dy), (base + sx * 6, 9), 7)
        tri(img, (base - sx * 3, 9), (base + sx * 1, 3 + dy), (base + sx * 5, 8), 1)
        tri(img, (base - sx * 1, 8), (base + sx * 1, 5 + dy), (base + sx * 3, 8), 4)

    ellipse(img, 40, 16, 13, 10, 7)                        # head
    ellipse(img, 40, 16, 12, 9, 1)
    for x in (37, 40, 43):                                 # forehead stripes
        line(img, (x, 8), (x, 10), 2)
    ellipse(img, 40, 20, 5.5, 3.6, 3)                      # muzzle

    blink = frame in (8, 9)
    for sx in (-1, 1):                                     # eyes
        ex = 40 + sx * 6
        if blink:
            line(img, (ex - 2, 15), (ex + 2, 15), 6)
        else:
            ellipse(img, ex, 15, 2.6, 2.6, 6)
            ellipse(img, ex, 15, 2.0, 2.0, 5)
            ellipse(img, ex, 15, 0.9, 1.7, 6)
            px(img, ex - 1, 14, 3)                         # glint

    tri(img, (39, 18), (41, 18), (40, 19), 4)              # nose
    px(img, 40, 20, 6)                                     # mouth
    px(img, 39, 21, 6)
    px(img, 41, 21, 6)
    for sx in (-1, 1):                                     # whiskers
        for k, dy in enumerate((-1, 1)):
            line(img, (40 + sx * 7, 19 + dy), (40 + sx * 14, 18 + dy * 2), 8)
    return img


# ---------------------------------------------------------------- GIF writer
def lzw_encode(indices, min_code):
    clear = 1 << min_code
    eoi = clear + 1
    out = bytearray()
    bitbuf = 0
    nbits = 0

    def emit(code, width):
        nonlocal bitbuf, nbits
        bitbuf |= code << nbits
        nbits += width
        while nbits >= 8:
            out.append(bitbuf & 0xFF)
            bitbuf >>= 8
            nbits -= 8

    def fresh():
        return {bytes([i]): i for i in range(clear)}

    table = fresh()
    next_code = eoi + 1
    width = min_code + 1
    emit(clear, width)
    cur = b""
    for v in indices:
        nxt = cur + bytes([v])
        if nxt in table:
            cur = nxt
            continue
        emit(table[cur], width)
        if next_code < 4096:
            table[nxt] = next_code
            next_code += 1
            if next_code > (1 << width) and width < 12:
                width += 1
        else:
            emit(clear, width)
            table = fresh()
            next_code = eoi + 1
            width = min_code + 1
        cur = bytes([v])
    if cur:
        emit(table[cur], width)
    emit(eoi, width)
    if nbits:
        out.append(bitbuf & 0xFF)
    return bytes(out)


def sub_blocks(data):
    out = bytearray()
    for i in range(0, len(data), 255):
        chunk = data[i:i + 255]
        out.append(len(chunk))
        out += chunk
    out.append(0)
    return bytes(out)


def scaled_indices(img):
    rows = []
    for row in img:
        wide = [c for c in row for _ in range(SCALE)]
        rows.extend([wide] * SCALE)
    return [c for r in rows for c in r]


def write_gif(path, frames):
    w, h = W * SCALE, H * SCALE
    out = bytearray(b"GIF89a")
    out += struct.pack("<HHBBB", w, h, 0xF3, 0, 0)         # 16-entry global table
    for r, g, b in PAL:
        out += bytes((r, g, b))
    out += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"   # loop forever
    for img in frames:
        out += b"\x21\xF9\x04" + bytes((0x00,)) + struct.pack("<H", DELAY_CS) + b"\x00\x00"
        out += b"\x2C" + struct.pack("<HHHHB", 0, 0, w, h, 0)
        out += bytes((4,)) + sub_blocks(lzw_encode(scaled_indices(img), 4))
    out += b"\x3B"
    with open(path, "wb") as f:
        f.write(out)
    return len(out)


# ------------------------------------------------------------ check / preview
def lzw_decode(data, min_code, count):
    clear = 1 << min_code
    eoi = clear + 1
    bitpos = 0
    out = []

    def read(width):
        nonlocal bitpos
        v = 0
        for i in range(width):
            byte = data[(bitpos + i) >> 3]
            v |= ((byte >> ((bitpos + i) & 7)) & 1) << i
        bitpos += width
        return v

    table = {}
    width = min_code + 1
    next_code = eoi + 1
    prev = None
    while len(out) < count:
        code = read(width)
        if code == clear:
            table = {i: bytes([i]) for i in range(clear)}
            width = min_code + 1
            next_code = eoi + 1
            prev = None
            continue
        if code == eoi:
            break
        if code in table:
            entry = table[code]
        elif prev is not None:
            entry = prev + prev[:1]
        else:
            raise ValueError("bad LZW stream")
        out.extend(entry)
        if prev is not None and next_code < 4096:
            table[next_code] = prev + entry[:1]
            next_code += 1
            if next_code >= (1 << width) and width < 12:
                width += 1
        prev = entry
    return out[:count]


def read_gif_frames(path):
    d = open(path, "rb").read()
    assert d[:6] == b"GIF89a"
    w, h, flags = struct.unpack("<HHB", d[6:11])
    pos = 13 + 3 * (1 << ((flags & 7) + 1))
    frames = []
    while d[pos] != 0x3B:
        if d[pos] == 0x21:
            pos += 2
            while d[pos]:
                pos += d[pos] + 1
            pos += 1
        elif d[pos] == 0x2C:
            pos += 10
            mc = d[pos]
            pos += 1
            raw = bytearray()
            while d[pos]:
                raw += d[pos + 1:pos + 1 + d[pos]]
                pos += d[pos] + 1
            pos += 1
            frames.append(lzw_decode(bytes(raw), mc, w * h))
        else:
            raise ValueError("unexpected block %#x" % d[pos])
    return w, h, frames


def write_png(path, width, height, rgb_rows):
    raw = b"".join(b"\x00" + bytes(r) for r in rgb_rows)

    def chunk(tag, body):
        c = struct.pack(">I", len(body)) + tag + body
        return c + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = args[0] if args else "gifs/cat.gif"
    frames = [cat(i) for i in range(FRAMES)]
    import os
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    size = write_gif(out, frames)
    print("wrote %s: %d bytes, %d frames, %dx%d" % (out, size, FRAMES, W * SCALE, H * SCALE))
    if "--check" in sys.argv:
        w, h, dec = read_gif_frames(out)
        for i, img in enumerate(frames):
            assert dec[i] == scaled_indices(img), "frame %d differs" % i
        print("round-trip OK: all %d frames decode identically" % len(dec))
        pick = [0, 3, 4, 8]
        sheet = []
        for y in range(h):
            row = []
            for f in pick:
                for x in range(w):
                    row.extend(PAL[dec[f][y * w + x]])
            sheet.append(row)
        write_png(out + ".preview.png", w * len(pick), h, sheet)
        print("preview:", out + ".preview.png")


if __name__ == "__main__":
    main()
