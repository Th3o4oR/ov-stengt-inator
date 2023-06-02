import color
import network
import machine
import time

# Network stuff
NETWORKS: dict
NETWORK_NAMES: list[str]
WLAN_OBJECT: network.WLAN
PING_URL: str # For checking internet connection

# API stuff
API_URL: str
API_INTERVAL: int

# Hardware stuff
ONBOARD_LED_PIN: machine.Pin

# Colors
COLOR_DOOR_OPEN:       color.Color
COLOR_DOOR_CLOSED:     color.Color
COLOR_API_FAIL:        color.Color
COLOR_WLAN_CONNECTING: color.Color
COLOR_PINGING:         color.Color

# Color thread
COLOR_MAPPING: dict[str, color.Color]
DISPLAY_COLOR_CURR: color.Color
DISPLAY_COLOR_PREV: color.Color
ACTUAL_COLOR_CURR:  color.Color
ACTUAL_COLOR_PREV:  color.Color
COLOR_CHANGE_TIME: int

BLINK_FREQUENCY: float
FADE_DURATION:   float
BRIGHTNESS:      float
COLOR_THREAD_EXIT: bool

def colors_init() -> None:
    # Initialize colors
    COLOR_MAPPING = {
        "red":    color.Color(1, 0,    0, "red"),
        "green":  color.Color(0, 1,    0, "green"),
        "blue":   color.Color(0, 0,    1, "blue"),
        "yellow": color.Color(1, 0.75, 0, "yellow"),
        "purple": color.Color(1, 0,    1, "purple"),
        "black":  color.Color(0, 0,    0, "black")
    }
    DISPLAY_COLOR_CURR = COLOR_MAPPING["black"]
    DISPLAY_COLOR_PREV = COLOR_MAPPING["black"]
    ACTUAL_COLOR_CURR  = COLOR_MAPPING["black"]
    ACTUAL_COLOR_PREV  = COLOR_MAPPING["black"]
    COLOR_CHANGE_TIME  = time.ticks_cpu()

    # Initialize thread variables
    COLOR_THREAD_EXIT = False

    # The following variables are overridden in main.py, as they are read from the config file
    BLINK_FREQUENCY = 0
    FADE_DURATION   = 1
    BRIGHTNESS      = 0.5
