/*
 * corne_dongle 160x128 status screen: shared layout constants and helpers.
 *
 *   +--------------------------------------+  y = 0
 *   | USB      L [###] 78     R [###] 92   |  top bar: output + both halves
 *   +--------------------------------------+  y = TOP_H
 *   |                                      |
 *   |            middle strip              |  typing cat (160x84) + restart reason
 *   |                                      |
 *   +--------------------------------------+  y = TOP_H + MID_H
 *   | ==== layer colour stripe ==========  |
 *   |               QWERTY                 |  bottom bar: active layer
 *   +--------------------------------------+  y = 128
 */
#pragma once

#include <lvgl.h>

#define SCREEN_W 160
#define SCREEN_H 128
#define TOP_H 20
#define MID_H 84
#define BOTTOM_H (SCREEN_H - TOP_H - MID_H)

/* Light theme: neutrals are the dark theme's inverted; accent colours stay true. */
#define COLOR_BG 0xEFEDE6
#define COLOR_BAR 0xE3DFCF
#define COLOR_TEXT 0x191711
#define COLOR_DIM 0xA59F8F
#define COLOR_GOOD 0x5CD67A
#define COLOR_WARN 0xFFB347
#define COLOR_BAD 0xFF5C5C
#define COLOR_BLE 0x4DA3FF
#define COLOR_VIOLET 0xB07CFF

/* A plain rectangle: no theme styles, no border, no padding, not scrollable. */
static inline lv_obj_t *dongle_box(lv_obj_t *parent, lv_coord_t x, lv_coord_t y, lv_coord_t w,
                                   lv_coord_t h, uint32_t bg) {
    lv_obj_t *o = lv_obj_create(parent);
    lv_obj_remove_style_all(o);
    lv_obj_set_pos(o, x, y);
    lv_obj_set_size(o, w, h);
    lv_obj_set_style_bg_color(o, lv_color_hex(bg), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(o, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(o, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);
    return o;
}

static inline lv_obj_t *dongle_label(lv_obj_t *parent, const lv_font_t *font, uint32_t color) {
    lv_obj_t *l = lv_label_create(parent);
    lv_obj_set_style_text_font(l, font, LV_PART_MAIN);
    lv_obj_set_style_text_color(l, lv_color_hex(color), LV_PART_MAIN);
    return l;
}

/*
 * Bit n set = key position n is on the LEFT half (48 positions). Derived from
 * default_transform in corne_dongle.overlay: columns 0-6 are the left half,
 * columns 7-13 the right half (right half uses col-offset 7).
 * Left positions: 0-5, 13-18, 28-34, 42-44.
 */
#define DONGLE_LEFT_POSITIONS 0x1c07f007e03fULL
#define DONGLE_POSITION_COUNT 48

static inline bool dongle_position_is_left(uint32_t position) {
    return position < DONGLE_POSITION_COUNT && ((DONGLE_LEFT_POSITIONS >> position) & 1ULL);
}

/* Which half a key position belongs to. Also indexes per-side arrays. */
enum dongle_side { DONGLE_SIDE_LEFT, DONGLE_SIDE_RIGHT };

static inline enum dongle_side dongle_position_side(uint32_t position) {
    return dongle_position_is_left(position) ? DONGLE_SIDE_LEFT : DONGLE_SIDE_RIGHT;
}

void dongle_output_init(lv_obj_t *top_bar);
void dongle_halves_init(lv_obj_t *top_bar);
void dongle_layer_init(lv_obj_t *bottom_bar);
void dongle_cat_init(lv_obj_t *middle);
void dongle_reset_reason_init(lv_obj_t *middle);
