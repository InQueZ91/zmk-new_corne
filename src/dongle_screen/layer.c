/*
 * Active layer (bottom bar): layer name in a per-layer colour, with a colour stripe.
 * Uses the keymap's display-name (or the name set in ZMK Studio).
 */
#include <stdio.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/keymap.h>
#include <zmk/events/layer_state_changed.h>

#include <dongle_screen/dongle_screen.h>

/* Colours by layer index: QWERTY, Game, 12#?, NavPad, Mouse&Fn, Setting */
static const uint32_t layer_colors[] = {0x4DA3FF, 0xFF5C5C, 0x5CD67A,
                                        0xFFB347, 0xB07CFF, 0xE6E8EE};

static lv_obj_t *layer_stripe;
static lv_obj_t *layer_label;

struct layer_state {
    zmk_keymap_layer_index_t index;
    const char *name;
};

static struct layer_state layer_get_state(const zmk_event_t *eh) {
    ARG_UNUSED(eh);
    zmk_keymap_layer_index_t index = zmk_keymap_highest_layer_active();
    return (struct layer_state){
        .index = index,
        .name = zmk_keymap_layer_name(zmk_keymap_layer_index_to_id(index)),
    };
}

static void layer_update_cb(struct layer_state s) {
    if (layer_label == NULL) {
        return;
    }
    uint32_t color = s.index < ARRAY_SIZE(layer_colors) ? layer_colors[s.index] : COLOR_TEXT;

    if (s.name != NULL && s.name[0] != '\0') {
        lv_label_set_text(layer_label, s.name);
    } else {
        char text[12];
        snprintf(text, sizeof(text), "Layer %u", (unsigned)s.index);
        lv_label_set_text(layer_label, text);
    }
    lv_obj_set_style_text_color(layer_label, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_bg_color(layer_stripe, lv_color_hex(color), LV_PART_MAIN);
}

ZMK_DISPLAY_WIDGET_LISTENER(w_layer, struct layer_state, layer_update_cb, layer_get_state)
ZMK_SUBSCRIPTION(w_layer, zmk_layer_state_changed);

void dongle_layer_init(lv_obj_t *bottom_bar) {
    layer_stripe = dongle_box(bottom_bar, 0, 0, SCREEN_W, 2, COLOR_DIM);

    layer_label = dongle_label(bottom_bar, &lv_font_montserrat_20, COLOR_TEXT);
    lv_obj_set_width(layer_label, SCREEN_W);
    lv_label_set_long_mode(layer_label, LV_LABEL_LONG_CLIP);
    lv_obj_set_style_text_align(layer_label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_obj_align(layer_label, LV_ALIGN_CENTER, 0, 1);

    w_layer_init();
}
