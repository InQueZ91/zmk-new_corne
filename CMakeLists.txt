# This repo is loaded as a Zephyr module by ZMK's build workflow (zephyr/module.yml).
# Only the dongle enables CONFIG_CORNE_DONGLE_SCREEN; the halves compile nothing here.
if(CONFIG_CORNE_DONGLE_SCREEN)
  zephyr_library()
  # ZMK's own headers are private to the app target, so add them explicitly.
  zephyr_library_include_directories(${APPLICATION_SOURCE_DIR}/include)
  zephyr_library_include_directories(include)
  zephyr_library_sources(
    src/dongle_screen/status_screen.c
    src/dongle_screen/halves.c
    src/dongle_screen/output.c
    src/dongle_screen/layer.c
  )
endif()
