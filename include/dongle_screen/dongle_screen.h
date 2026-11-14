/*
 * corne_dongle 160x128 status screen: shared layout constants and helpers.
 *
 *   +--------------------------------------+  y = 0
 *   | USB      L [###] 78     R [###] 92   |  top bar: output + both halves
 *   +--------------------------------------+  y = TOP_H
 *   |                                      |
 *   |            middle strip              |  reserved for the GIF (160x84)
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

#define COLOR_BG 0x101219
#define COLOR_BAR 0x1C2030
#define COLOR_TEXT 0xE6E8EE
#define COLOR_DIM 0x5A6070
#define COLOR_GOOD 0x5CD67A
#define COLOR_WARN 0xFFB347
#define COLOR_BAD 0xFF5C5C
#define COLOR_BLE 0x4DA3FF

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

void dongle_output_init(lv_obj_t *top_bar);
void dongle_halves_init(lv_obj_t *top_bar);
void dongle_layer_init(lv_obj_t *bottom_bar);
