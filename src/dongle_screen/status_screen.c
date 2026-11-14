/*
 * corne_dongle custom status screen (ZMK v0.3.0, CONFIG_ZMK_DISPLAY_STATUS_SCREEN_CUSTOM).
 * ZMK calls zmk_display_status_screen() once, on the display work queue.
 */
#include <zephyr/kernel.h>
#include <zmk/display.h>

#include <dongle_screen/dongle_screen.h>

lv_obj_t *zmk_display_status_screen(void) {
    lv_obj_t *screen = lv_obj_create(NULL);
    lv_obj_remove_style_all(screen);
    lv_obj_set_style_bg_color(screen, lv_color_hex(COLOR_BG), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(screen, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *top = dongle_box(screen, 0, 0, SCREEN_W, TOP_H, COLOR_BAR);
    dongle_output_init(top);
    dongle_halves_init(top);

    /* Middle strip: typing cat, with the last restart reason on top for a minute. */
    lv_obj_t *mid = dongle_box(screen, 0, TOP_H, SCREEN_W, MID_H, COLOR_BG);
    dongle_cat_init(mid);
    dongle_reset_reason_init(mid);

    lv_obj_t *bottom = dongle_box(screen, 0, TOP_H + MID_H, SCREEN_W, BOTTOM_H, COLOR_BAR);
    dongle_layer_init(bottom);

    return screen;
}
