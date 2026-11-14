/*
 * Left / right half indicators (top bar): battery and connection merged.
 *
 *   L [####  ] 78     coloured by level: green > 50, amber > 20, red <= 20
 *   L [      ] --     grey: half offline
 *
 * How connection is known: when a half disconnects, ZMK v0.3.0's split central
 * reports battery level 0 for it (split/bluetooth/central.c), and it fetches the
 * real level again after reconnecting. So level 0 = offline.
 *
 * How left/right is known: ZMK numbers the halves by connection order (slot 0/1),
 * not by side. Every key press carries its slot (event->source) and its key
 * position; positions on the left half are listed in LEFT_POSITIONS. The first key
 * press after boot fixes the mapping. Until then slot 0 is shown as L (a guess).
 * Positions on the left half: DONGLE_LEFT_POSITIONS in dongle_screen.h.
 */
#include <stdio.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/events/battery_state_changed.h>
#include <zmk/events/position_state_changed.h>
#include <zmk/split/central.h>

#include <dongle_screen/dongle_screen.h>

#define HALVES 2
#define SIDE_LEFT 0
#define SIDE_RIGHT 1

/* side_of_slot[slot] = SIDE_LEFT / SIDE_RIGHT. Written from the event thread,
 * read on the display queue; single bytes, so no tearing. */
static volatile uint8_t side_of_slot[HALVES] = {SIDE_LEFT, SIDE_RIGHT};

struct half_widget {
    lv_obj_t *name;
    lv_obj_t *body;
    lv_obj_t *fill;
    lv_obj_t *nub;
    lv_obj_t *pct;
};
static struct half_widget halves[HALVES]; /* indexed by side */
static bool halves_ready;

struct halves_state {
    uint8_t level[HALVES]; /* indexed by slot; 0 = offline / unknown */
};
static uint8_t level_cache[HALVES];

#define BODY_W 20
#define BODY_H 10

static void draw_half(struct half_widget *w, uint8_t level) {
    bool online = level > 0;
    uint32_t color = !online       ? COLOR_DIM
                     : level > 50 ? COLOR_GOOD
                     : level > 20 ? COLOR_WARN
                                  : COLOR_BAD;
    uint32_t frame = online ? COLOR_TEXT : COLOR_DIM;

    lv_obj_set_style_text_color(w->name, lv_color_hex(online ? COLOR_TEXT : COLOR_DIM),
                                LV_PART_MAIN);
    lv_obj_set_style_border_color(w->body, lv_color_hex(frame), LV_PART_MAIN);
    lv_obj_set_style_bg_color(w->nub, lv_color_hex(frame), LV_PART_MAIN);

    lv_coord_t fill_w = online ? MAX(1, (BODY_W - 4) * MIN(level, 100) / 100) : 0;
    lv_obj_set_width(w->fill, fill_w);
    lv_obj_set_style_bg_color(w->fill, lv_color_hex(color), LV_PART_MAIN);

    if (online) {
        char text[4];
        snprintf(text, sizeof(text), "%u", (unsigned)MIN(level, 100));
        lv_label_set_text(w->pct, text);
    } else {
        lv_label_set_text(w->pct, "--");
    }
    lv_obj_set_style_text_color(w->pct, lv_color_hex(color), LV_PART_MAIN);
}

static struct halves_state halves_get_state(const zmk_event_t *eh) {
    const struct zmk_peripheral_battery_state_changed *ev =
        eh ? as_zmk_peripheral_battery_state_changed(eh) : NULL;

    if (ev != NULL && ev->source < HALVES) {
        level_cache[ev->source] = ev->state_of_charge;
    } else if (ev == NULL) {
        for (uint8_t i = 0; i < HALVES; i++) {
            uint8_t lvl = 0;
            if (zmk_split_central_get_peripheral_battery_level(i, &lvl) == 0) {
                level_cache[i] = lvl;
            }
        }
    }

    struct halves_state s;
    memcpy(s.level, level_cache, sizeof(s.level));
    return s;
}

static void halves_update_cb(struct halves_state s) {
    if (!halves_ready) {
        return;
    }
    for (uint8_t slot = 0; slot < HALVES; slot++) {
        draw_half(&halves[side_of_slot[slot] & 1], s.level[slot]);
    }
}

ZMK_DISPLAY_WIDGET_LISTENER(w_halves, struct halves_state, halves_update_cb, halves_get_state)
ZMK_SUBSCRIPTION(w_halves, zmk_peripheral_battery_state_changed);

/* Learn which slot is the left half from key presses. Never consumes the event. */
static int side_listener_cb(const zmk_event_t *eh) {
    const struct zmk_position_state_changed *ev = as_zmk_position_state_changed(eh);

    if (ev == NULL || !ev->state || ev->source >= HALVES ||
        ev->position >= DONGLE_POSITION_COUNT) {
        return ZMK_EV_EVENT_BUBBLE;
    }

    uint8_t side = dongle_position_is_left(ev->position) ? SIDE_LEFT : SIDE_RIGHT;
    if (side_of_slot[ev->source] != side) {
        side_of_slot[ev->source] = side;
        side_of_slot[1 - ev->source] = 1 - side;
        if (zmk_display_is_initialized()) {
            k_work_submit_to_queue(zmk_display_work_q(), &w_halves_work);
        }
    }
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(dongle_side, side_listener_cb);
ZMK_SUBSCRIPTION(dongle_side, zmk_position_state_changed);

static void create_half(struct half_widget *w, lv_obj_t *parent, lv_coord_t x, const char *name) {
    w->name = dongle_label(parent, &lv_font_montserrat_14, COLOR_DIM);
    lv_label_set_text(w->name, name);
    lv_obj_align(w->name, LV_ALIGN_LEFT_MID, x, 0);

    w->body = lv_obj_create(parent);
    lv_obj_remove_style_all(w->body);
    lv_obj_set_size(w->body, BODY_W, BODY_H);
    lv_obj_align(w->body, LV_ALIGN_LEFT_MID, x + 13, 0);
    lv_obj_set_style_border_width(w->body, 1, LV_PART_MAIN);
    lv_obj_set_style_border_color(w->body, lv_color_hex(COLOR_DIM), LV_PART_MAIN);
    lv_obj_set_style_radius(w->body, 2, LV_PART_MAIN);
    lv_obj_clear_flag(w->body, LV_OBJ_FLAG_SCROLLABLE | LV_OBJ_FLAG_CLICKABLE);

    w->fill = dongle_box(w->body, 2, 2, 0, BODY_H - 4, COLOR_DIM);

    w->nub = dongle_box(parent, 0, 0, 2, 4, COLOR_DIM);
    lv_obj_align(w->nub, LV_ALIGN_LEFT_MID, x + 13 + BODY_W, 0);

    w->pct = dongle_label(parent, &lv_font_montserrat_12, COLOR_DIM);
    lv_label_set_text(w->pct, "--");
    lv_obj_align(w->pct, LV_ALIGN_LEFT_MID, x + 13 + BODY_W + 5, 0);
}

void dongle_halves_init(lv_obj_t *top_bar) {
    create_half(&halves[SIDE_LEFT], top_bar, 30, "L");
    create_half(&halves[SIDE_RIGHT], top_bar, 96, "R");
    halves_ready = true;
    w_halves_init();
}
