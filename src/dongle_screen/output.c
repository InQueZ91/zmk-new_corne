/*
 * Output indicator (top-left): where keystrokes go.
 *   USB icon      white = PC has the keyboard, grey = USB powered but not ready
 *   BT icon + n   blue  = BLE profile n connected, amber = not connected
 */
#include <zephyr/kernel.h>
#include <zmk/display.h>
#include <zmk/event_manager.h>
#include <zmk/endpoints.h>
#include <zmk/events/endpoint_changed.h>
#include <zmk/ble.h>
#include <zmk/events/ble_active_profile_changed.h>
#include <zmk/usb.h>
#include <zmk/events/usb_conn_state_changed.h>

#include <dongle_screen/dongle_screen.h>

static lv_obj_t *output_label;

struct output_state {
    enum zmk_transport transport;
    int profile;
    bool usb_ready;
    bool ble_connected;
};

static struct output_state output_get_state(const zmk_event_t *eh) {
    ARG_UNUSED(eh);
    return (struct output_state){
        .transport = zmk_endpoints_selected().transport,
        .profile = zmk_ble_active_profile_index(),
        .usb_ready = zmk_usb_is_hid_ready(),
        .ble_connected = zmk_ble_active_profile_is_connected(),
    };
}

static void output_update_cb(struct output_state s) {
    if (output_label == NULL) {
        return;
    }
    char text[16]; /* 3-byte UTF-8 symbol + up to 11 digits + NUL */
    uint32_t color;

    if (s.transport == ZMK_TRANSPORT_USB) {
        snprintf(text, sizeof(text), LV_SYMBOL_USB);
        color = s.usb_ready ? COLOR_TEXT : COLOR_DIM;
    } else {
        snprintf(text, sizeof(text), LV_SYMBOL_BLUETOOTH "%d", s.profile + 1);
        color = s.ble_connected ? COLOR_BLE : COLOR_WARN;
    }
    lv_label_set_text(output_label, text);
    lv_obj_set_style_text_color(output_label, lv_color_hex(color), LV_PART_MAIN);
}

ZMK_DISPLAY_WIDGET_LISTENER(w_output, struct output_state, output_update_cb, output_get_state)
ZMK_SUBSCRIPTION(w_output, zmk_endpoint_changed);
ZMK_SUBSCRIPTION(w_output, zmk_ble_active_profile_changed);
ZMK_SUBSCRIPTION(w_output, zmk_usb_conn_state_changed);

void dongle_output_init(lv_obj_t *top_bar) {
    output_label = dongle_label(top_bar, &lv_font_montserrat_14, COLOR_TEXT);
    lv_obj_align(output_label, LV_ALIGN_LEFT_MID, 4, 0);
    w_output_init();
}
