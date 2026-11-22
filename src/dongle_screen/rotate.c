/*
 * &rotate_screen: toggles the dongle screen between normal and 180 degrees.
 * LVGL software rotation (the panel's MADCTL is untouched). Runs on the
 * dongle only (central locality); the halves never see it. Not remembered
 * across reboots: the screen starts in the normal orientation.
 */
#define DT_DRV_COMPAT zmk_behavior_screen_rotate

#include <zephyr/device.h>
#include <zephyr/kernel.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include <zmk/display.h>

#include <dongle_screen/dongle_screen.h>

static bool rotated;

/* LVGL is only touched from the display work queue. */
static void rotate_work_cb(struct k_work *work) {
    ARG_UNUSED(work);
    lv_disp_t *disp = lv_disp_get_default();
    if (disp == NULL) {
        return;
    }
    rotated = !rotated;
    disp->driver->sw_rotate = 1;
    lv_disp_set_rotation(disp, rotated ? LV_DISP_ROT_180 : LV_DISP_ROT_NONE);
    lv_obj_invalidate(lv_scr_act());
}
static K_WORK_DEFINE(rotate_work, rotate_work_cb);

static int on_pressed(struct zmk_behavior_binding *binding,
                      struct zmk_behavior_binding_event event) {
    ARG_UNUSED(binding);
    ARG_UNUSED(event);
    if (zmk_display_is_initialized()) {
        k_work_submit_to_queue(zmk_display_work_q(), &rotate_work);
    }
    return ZMK_BEHAVIOR_OPAQUE;
}

static int on_released(struct zmk_behavior_binding *binding,
                       struct zmk_behavior_binding_event event) {
    ARG_UNUSED(binding);
    ARG_UNUSED(event);
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api rotate_api = {
    .binding_pressed = on_pressed,
    .binding_released = on_released,
    .locality = BEHAVIOR_LOCALITY_CENTRAL,
};

BEHAVIOR_DT_INST_DEFINE(0, NULL, NULL, NULL, NULL, POST_KERNEL, CONFIG_KERNEL_INIT_PRIORITY_DEFAULT,
                        &rotate_api);
