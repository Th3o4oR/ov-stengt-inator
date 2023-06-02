import color
import network
import machine
# import time

# Variables overridden by config file
NETWORKS:      dict[int, dict] = {}
NETWORK_NAMES: list[str]       = []
PING_URL:      str = ""
API_URL:       str = ""
API_INTERVAL:  int = 60

# Global variables
WLAN_OBJECT: network.WLAN = network.WLAN(network.STA_IF)

# Hardware stuff
ONBOARD_LED_PIN: machine.Pin = machine.Pin("LED", machine.Pin.OUT)

# Initialize colors
COLOR_MAPPING: dict[str, color.Color] = {
    "red":    color.Color(1, 0,    0, "red"),
    "green":  color.Color(0, 1,    0, "green"),
    "blue":   color.Color(0, 0,    1, "blue"),
    "yellow": color.Color(1, 0.75, 0, "yellow"),
    "purple": color.Color(1, 0,    1, "purple"),
    "black":  color.Color(0, 0,    0, "black")
}
DISPLAY_COLOR_CURR: color.Color = COLOR_MAPPING["black"]
DISPLAY_COLOR_PREV: color.Color = COLOR_MAPPING["black"]
ACTUAL_COLOR_CURR:  color.Color = COLOR_MAPPING["black"]
ACTUAL_COLOR_PREV:  color.Color = COLOR_MAPPING["black"]
COLOR_CHANGE_TIME: int = 0

# Dummy values, these should be overwritten by config.json
BLINK_STATE:     bool  = False
BLINK_FREQUENCY: float = 0.0
FADE_DURATION:   float = 1.0
BRIGHTNESS:      float = 0.5
COLOR_THREAD_EXIT: bool = False

# Colors (also dummy values)
COLOR_DOOR_OPEN:       color.Color = COLOR_MAPPING["yellow"]
COLOR_DOOR_CLOSED:     color.Color = COLOR_MAPPING["yellow"]
COLOR_API_FAIL:        color.Color = COLOR_MAPPING["yellow"]
COLOR_WLAN_CONNECTING: color.Color = COLOR_MAPPING["yellow"]
COLOR_PINGING:         color.Color = COLOR_MAPPING["yellow"]
