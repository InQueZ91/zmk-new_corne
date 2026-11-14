/*
 * Shows why the dongle last started, in small text over the middle strip, for
 * SHOW_MS after boot. Read once from the nRF52 RESETREAS register (Zephyr hwinfo),
 * then cleared so the next boot reports only its own cause.
 *
 *   "Power on"          plugged in, or a power dip (the nRF52 has no separate brownout flag)
 *   "Restart: software" Zephyr rebooted itself: a crash (fatal error), &sys_reset,
 *                       or a firmware update / bootloader exit
 *   "Restart: lockup"   the CPU hit a hard fault it could not handle
 *   "Restart: watchdog" watchdog timeout
 *   "Restart: button"   reset pin (double-tap for bootloader also counts)
 */
#include <stdio.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/hwinfo.h>
#include <zmk/display.h>

#include <dongle_screen/dongle_screen.h>

#define SHOW_MS 60000

static lv_obj_t *reason_label;
static struct k_work_delayable hide_work;

static void hide_cb(struct k_work *work) {
    ARG_UNUSED(work);
    if (reason_label != NULL) {
        lv_obj_add_flag(reason_label, LV_OBJ_FLAG_HIDDEN);
    }
}

static const char *reason_text(uint32_t cause, uint32_t *color) {
    *color = COLOR_DIM;
    if (cause & RESET_CPU_LOCKUP) {
        *color = COLOR_BAD;
        return "Restart: lockup";
    }
    if (cause & RESET_WATCHDOG) {
        *color = COLOR_BAD;
        return "Restart: watchdog";
    }
    if (cause & RESET_SOFTWARE) {
        *color = COLOR_WARN;
        return "Restart: software";
    }
    if (cause & RESET_PIN) {
        return "Restart: button";
    }
    if (cause == 0 || (cause & (RESET_POR | RESET_BROWNOUT))) {
        return "Power on";
    }
    return NULL;
}

void dongle_reset_reason_init(lv_obj_t *middle) {
    uint32_t cause = 0;
    if (hwinfo_get_reset_cause(&cause) != 0) {
        return;
    }
    hwinfo_clear_reset_cause();

    uint32_t color;
    const char *text = reason_text(cause, &color);
    char buf[24];
    if (text == NULL) {
        snprintf(buf, sizeof(buf), "Reset 0x%x", (unsigned)cause);
        text = buf;
    }

    reason_label = dongle_label(middle, &lv_font_montserrat_12, color);
    lv_label_set_text(reason_label, text);
    lv_obj_align(reason_label, LV_ALIGN_TOP_LEFT, 3, 1);

    k_work_init_delayable(&hide_work, hide_cb);
    k_work_schedule_for_queue(zmk_display_work_q(), &hide_work, K_MSEC(SHOW_MS));
}
