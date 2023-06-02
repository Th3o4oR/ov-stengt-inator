import machine
import time
import math
import _thread

import color
import globals

RGB_PIN_RED:   machine.Pin = machine.Pin("GP28", machine.Pin.OUT)
RGB_PIN_GREEN: machine.Pin = machine.Pin("GP27", machine.Pin.OUT)
RGB_PIN_BLUE:  machine.Pin = machine.Pin("GP26", machine.Pin.OUT)

RGB_PWM_RED:   machine.PWM = machine.PWM(RGB_PIN_RED)
RGB_PWM_GREEN: machine.PWM = machine.PWM(RGB_PIN_GREEN)
RGB_PWM_BLUE:  machine.PWM = machine.PWM(RGB_PIN_BLUE)

PWM_FREQ: int = 100000
PWM_DUTY_MAX: int = 2**16-1
RGB_PWM_RED.freq(PWM_FREQ)
RGB_PWM_GREEN.freq(PWM_FREQ)
RGB_PWM_BLUE.freq(PWM_FREQ)

# Update RGB LED
def set_rgb(c: color.Color) -> None:
    c *= globals.BRIGHTNESS
    RGB_PWM_RED.duty_u16(int((1-c.red)*PWM_DUTY_MAX))
    RGB_PWM_GREEN.duty_u16(int((1-c.green)*PWM_DUTY_MAX))
    RGB_PWM_BLUE.duty_u16(int((1-c.blue)*PWM_DUTY_MAX))

# Update color variables
def change_color(c: color.Color, blink_freq: float = 0, fade_time: float | None = None) -> None:
    # Update previous and current colors
    globals.ACTUAL_COLOR_PREV = globals.ACTUAL_COLOR_CURR
    globals.ACTUAL_COLOR_CURR = c

    # Update previous and current display colors
    globals.DISPLAY_COLOR_PREV = globals.DISPLAY_COLOR_CURR
    globals.DISPLAY_COLOR_CURR = c

    # Set the time of change
    globals.COLOR_CHANGE_TIME = time.ticks_cpu()

    # Update blink frequency
    globals.BLINK_STATE = False
    globals.BLINK_FREQUENCY = blink_freq
    if (fade_time != None):
        globals.FADE_DURATION = fade_time

# Initialize variables required for color thread (and other threads relying on color thread)
def color_thread_init() -> None:
    # Initialize colors
    globals.COLOR_MAPPING = {
        "red":    color.Color(1, 0,    0, "red"),
        "green":  color.Color(0, 1,    0, "green"),
        "blue":   color.Color(0, 0,    1, "blue"),
        "yellow": color.Color(1, 0.75, 0, "yellow"),
        "purple": color.Color(1, 0,    1, "purple"),
        "black":  color.Color(0, 0,    0, "black")
    }
    globals.DISPLAY_COLOR_CURR = globals.COLOR_MAPPING["black"]
    globals.DISPLAY_COLOR_PREV = globals.COLOR_MAPPING["black"]
    globals.ACTUAL_COLOR_CURR  = globals.COLOR_MAPPING["black"]
    globals.ACTUAL_COLOR_PREV  = globals.COLOR_MAPPING["black"]
    globals.COLOR_CHANGE_TIME  = time.ticks_cpu()

    # Initialize thread variables
    globals.BLINK_STATE = False
    globals.COLOR_THREAD_EXIT = False

    # The following variables are overridden in main.py, as they are read from the config file
    globals.BLINK_FREQUENCY = 0
    globals.FADE_DURATION   = 1
    globals.BRIGHTNESS      = 0.5

# Function to be run as color thread
def color_thread() -> None:
    # Start thread
    fade_factor: float = 0
    should_blink: float = True
    while not globals.COLOR_THREAD_EXIT:
        # Get current time and time since last color change (in microseconds)
        t: float = float(time.ticks_cpu())
        dt: float = time.ticks_diff(int(t), globals.COLOR_CHANGE_TIME)
        
        # Rescale time to seconds
        t = pow(10, -6) * t
        dt = pow(10, -6) * dt
        
        # Blink when blink should occur
        should_blink = not (math.floor(2*dt*globals.BLINK_FREQUENCY)+1)%2
        if (should_blink and globals.BLINK_FREQUENCY != 0):
            globals.COLOR_CHANGE_TIME = time.ticks_cpu()
            globals.DISPLAY_COLOR_PREV = globals.DISPLAY_COLOR_CURR
            globals.DISPLAY_COLOR_CURR = [globals.COLOR_MAPPING["black"], globals.ACTUAL_COLOR_CURR][globals.BLINK_STATE] # Indexing magic
            globals.BLINK_STATE = not globals.BLINK_STATE

        if (globals.FADE_DURATION == 0):
            set_rgb(globals.DISPLAY_COLOR_CURR * globals.BLINK_STATE)
        else:
            fade_factor = -math.cos(min(dt/globals.FADE_DURATION, 1)*math.pi)/2 + 0.5
            new_color: color.Color = globals.DISPLAY_COLOR_PREV*(1-fade_factor) + globals.DISPLAY_COLOR_CURR*fade_factor
            set_rgb(new_color)

    print("[Color thread] Terminating...")
    set_rgb(globals.COLOR_MAPPING["black"])

if __name__ == "__main__":
    try:
        color_thread_init()
        _thread.start_new_thread(color_thread, ())
        # time.sleep(0.1)
        print(globals.COLOR_MAPPING)

        change_color(globals.COLOR_MAPPING["red"], fade_time=0.5)
        time.sleep(0.5)
        change_color(globals.COLOR_MAPPING["black"], fade_time=0.5)
        time.sleep(0.5)
        change_color(globals.COLOR_MAPPING["blue"], fade_time=0.5, blink_freq=1)
        time.sleep(10)
        
        globals.COLOR_THREAD_EXIT = True
    except KeyboardInterrupt:
        globals.COLOR_THREAD_EXIT = True

