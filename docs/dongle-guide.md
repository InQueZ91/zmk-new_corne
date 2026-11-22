# Corne dongle guide

How this keyboard is set up, how to change things, and how to fix it when it breaks.
Written for future me. Branch: `dongle`. The old standalone setup is the tag `pre-dongle` (branch `main`).

## 1. How it works

```
 left half  ──BLE──┐
                   ├──►  dongle (nice!nano v2)  ──USB──►  PC
 right half ──BLE──┘     BLE central + USB keyboard
                         160x128 colour screen (ST7735)
```

- **Dongle:** the only "central". It talks USB to the PC and Bluetooth to both halves. Always plugged in, never sleeps.
- **Halves:** peripheral-only. They only work with the dongle (see section 7 to go back to standalone).
- **Keymap:** lives only in the repo, in `config/eyelash_corne.keymap`. ZMK Studio is removed, so nothing stored on the device can override it.
- **Firmware:** built by GitHub Actions on every push (`build.yaml`). Nothing is built locally.

## 2. Repo map

| Path | What it is |
|---|---|
| `config/eyelash_corne.keymap` | The keymap (shared by halves and dongle) |
| `config/boards/shields/corne_dongle/` | Dongle shield: `.overlay` (pins, display), `.conf` (settings), layout |
| `src/dongle_screen/` | Screen code: `status_screen.c`, `halves.c` (battery), `output.c` (USB/BT), `layer.c`, `cat.c` (typing cat), `reset_reason.c` |
| `src/dongle_screen/cat_frames.c` | **Generated** cat pictures. Do not edit by hand |
| `cat/base.png` | The hand-drawn character (160x84, both hands down). Source of all 5 poses |
| `scripts/make_cat_frames.py` | Builds the 5 poses from `cat/base.png` and writes `cat_frames.c` |
| `Kconfig`, `CMakeLists.txt`, `zephyr/module.yml` | Make the repo load as a Zephyr module so the screen code compiles for the dongle only |
| `build.yaml` | Which firmware files get built |
| `keymap-drawer/` | Auto-drawn picture of the keymap (a bot commits it after each push) |

## 3. Changing the keymap

1. Open the [Keymap Editor](https://nickcoutsos.github.io/keymap-editor/). Its GitHub integration is being shut down (maybe end of 2026), so use the **FileSystem** source in Chrome or Edge and pick the local repo folder. Edit `config/eyelash_corne.keymap`.
2. `git pull` first, because the keymap-drawer bot pushes commits too.
3. Commit and push.
4. Wait for the build (about 2 minutes), download the firmware, flash **only the dongle**. Keymap changes never need a flash of the halves.

Combos, macros and hold-tap timing are edited in the keymap file itself.

## 4. Getting the firmware

Go to the repo's **Actions** tab, open the latest "Build ZMK firmware" run, and download the artifact. Or:

```bash
gh run list --branch dongle --limit 3
gh run download <run-id> -n firmware -D firmware
```

| File | Flash to |
|---|---|
| `corne_dongle.uf2` | dongle (daily use) |
| `corne_dongle_logging.uf2` | dongle, only for debugging (needs a serial terminal) |
| `eyelash_corne_left.uf2` | left half |
| `eyelash_corne_right.uf2` | right half |
| `settings_reset_nice_nano_v2.uf2` | dongle, to wipe Bluetooth pairings |
| `settings_reset_eyelash_corne.uf2` | either half, to wipe pairings (built for the left board; assumed to work on the right, unverified) |

## 5. Flashing

**Bootloader mode:** double-tap the reset button on the board. A USB drive (e.g. `NICENANO`) appears. Drag the `.uf2` onto it; the board reboots by itself. No pins to short.

**Normal update (keymap or screen change):** flash the dongle only.

**Re-pair everything (halves and dongle stop talking, both halves show `--`):**
1. Flash `settings_reset` on the **dongle**, the **left half** and the **right half**.
2. Flash `corne_dongle.uf2` on the dongle.
3. Flash the left and right half firmware.
4. Power everything on; both halves should connect within a few seconds.

Skipping the reset on any one of the three can leave a stale pairing and the halves won't reconnect.

## 6. The screen

```
┌──────────────────────────────────────┐
│ USB    L [▓▓▓ ] 78    R [▓▓▓▓] 92    │  output + battery/connection per half
├──────────────────────────────────────┤
│  restart reason (first 60 s)         │
│              typing cat              │  160x84
├══════════════════════════════════════┤
│               QWERTY                 │  layer name, coloured per layer
└──────────────────────────────────────┘
```

- **Output icon:** USB is white when the PC has the keyboard, grey if only powered. Bluetooth shows the profile number.
- **Half indicator:** green above 50%, amber above 20%, red below. Grey with `--` means that half is disconnected. While a half is charging it reads 100% (voltage-based estimate, hardware limit).
- **L/R mapping:** ZMK numbers the halves by connection order. The screen learns which is left from the first key press after boot, so right after power-on it may be swapped for a moment.
- **Layer colours:** QWERTY blue, Game red, 12#? green, NavPad amber, Mouse&Fn purple, Setting white. Names come from `display-name` in the keymap.
- **Typing character:** a key on the left half keeps the left hand down (right lifted), the right half the opposite, both halves both hands down, nothing pressed lifts both. Eyes close and a `z` appears after 30 s idle.
- **Restart reason** (shown for 60 s after boot):
  - `Power on` (grey): plugged in, or a power dip.
  - `Restart: software` (amber): a crash, `&sys_reset`, or just after flashing.
  - `Restart: lockup` / `watchdog` (red): hard crash.
  - `Restart: button`: reset pin.
  - Unverified: the bootloader might clear the reset record before the firmware reads it. If every restart says `Power on`, use the logging build instead.

### Display wiring (ST7735, 128x160, SPI)

Pins as written in `corne_dongle.overlay` (nRF GPIO numbers, not the silkscreen labels on the nice!nano; match them to the board's pinout before rewiring):

| Display pin | nRF pin |
|---|---|
| SCK | P1.13 |
| SDA / MOSI | P1.11 |
| CS | P0.20 |
| DC (A0) | P0.17 |
| RESET | P0.22 |
| BLK (backlight) | P0.24 (driven directly, always on) |
| VCC / GND | 3.3 V / GND |

Panel settings that matter (all in the overlay, hard-won): height 128, x/y offset 0, `rgb-is-inverted` set, no `inversion-on` (the light theme is done in software: `COLOR_*` in `dongle_screen.h`; panel inversion would turn blue into orange), power/gamma values from the Longan Nano. The Adafruit values gave a blank white screen.

To rotate the screen 180 degrees: press the `&rotate_screen` key (Setting layer, third key of the top row on the left half). It toggles, and resets to normal after a reboot. Implemented as LVGL software rotation in `src/dongle_screen/rotate.c`. Fallback if that misbehaves: change `madctl` in the overlay from `0x78` to `0xB8` and reflash.

### RGB on the halves

The halves' LEDs are controlled by `&rgb_ug` keys, which the dongle handles and forwards over Bluetooth. For that the dongle needs RGB underglow compiled in, so it carries a one-LED dummy strip on P1.15 (nothing connected; see the overlay) and `CONFIG_ZMK_RGB_UNDERGLOW_EXT_POWER=n` so it never switches the ext-power rail that feeds the display. Untested on hardware: if RGB keys still do nothing, check the build log for the underglow symbols first.

## 7. Going back to standalone (no dongle)

The halves can't switch at runtime; it takes a reflash:
1. Flash `settings_reset` on both halves.
2. Flash the firmware from the `pre-dongle` tag (left half is the central there).
3. Re-pair with the PC.

To return to the dongle, do the "re-pair everything" steps in section 5.

## 8. Changing the character

The picture is `cat/base.png`: 160x84, transparent background, the "both hands down" pose. `scripts/make_cat_frames.py` derives the other four poses from it:

| Frame | How it is made |
|---|---|
| both | `base.png` as is |
| left / right | one hand (left or right half of the picture) lifted 5 px |
| idle | both hands lifted |
| sleep | eyes closed (eye rows/columns set in the script) + a small `z` |

To change it: edit or replace `cat/base.png` (keep 160x84), then

```bash
python -m pip install pillow
python scripts/make_cat_frames.py --preview preview.png
```

Look at `preview.png`, then commit `cat/` and `src/dongle_screen/cat_frames.c` and push. Only the dongle needs flashing.

Limits: the firmware format allows 16 colours; the script folds the art down to 15 plus the screen background automatically (the rarest colour merges into its nearest neighbour). If you redraw the character, the hand rows (`HAND_TOP`, `SPLIT`) and eye position (`EYES`, `EYE_ROWS`) at the top of the script must match your art. To draw all five poses by hand instead, the script's `frames()` function is the only place to change.

## 9. Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| Both halves show `--` but the dongle is fine | Stale pairing. Do the full re-pair (section 5) |
| Screen goes white, halves drop at the same time | Was a work-queue stall; the display now has its own thread and bigger stacks. If it returns, flash the logging build and read the serial output |
| Dongle restarts by itself | Read the restart reason on screen within 60 s. Try a USB 2.0 port or an extension cable (USB 3.0 interference was a suspect). Not yet root-caused |
| Screen blank white | Wrong panel settings (see section 6), or the display isn't powered/wired |
| Colours look wrong (red and blue swapped) | Byte-order/colour setting in `corne_dongle.conf` (`LV_COLOR_16_SWAP`); not seen so far |
| Repo keymap change doesn't show after flashing | Only possible if something is saved on the device. Flash `settings_reset` on the dongle, then the firmware |
| No Studio | Removed on purpose; edit the keymap in the repo |

**Debugging a disconnect:** flash `corne_dongle_logging.uf2`, open its USB serial port in a terminal at the moment of the problem. It is built at debug level because ZMK only prints the Bluetooth disconnect reason at that level. Go back to `corne_dongle.uf2` afterwards.

## 10. Open items

- Dongle self-restarts: cause unknown.
- Backlight dimming / idle-off: not done. BLK is driven straight from a GPIO; a transistor is advisable for dimming.
- SD card on the display board (to change pictures without flashing): idea only, nothing built. Needs 2 extra wires and is the riskiest part.
- Optional: Caps Lock indicator on the screen (ZMK v0.3.0 supports HID indicators).
- Versions: ZMK v0.3.0, Zephyr 3.5. Board names use the old style (`nice_nano_v2`).
