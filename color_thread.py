import machine
import time
import math
import _thread

import color
import globals

LED_PIN_RED:   machine.Pin = machine.Pin("GP28", machine.Pin.OUT)
LED_PIN_GREEN: machine.Pin = machine.Pin("GP27", machine.Pin.OUT)
LED_PIN_BLUE:  machine.Pin = machine.Pin("GP26", machine.Pin.OUT)

LED_PWM_RED:   machine.PWM = machine.PWM(LED_PIN_RED)
LED_PWM_GREEN: machine.PWM = machine.PWM(LED_PIN_GREEN)
LED_PWM_BLUE:  machine.PWM = machine.PWM(LED_PIN_BLUE)

PWM_FREQ: int = 100000
PWM_DUTY_MAX: int = 2**16-1
LED_PWM_RED.freq(PWM_FREQ)
LED_PWM_GREEN.freq(PWM_FREQ)
LED_PWM_BLUE.freq(PWM_FREQ)

# Update RGB LED
def set_rgb(c: color.Color) -> None:
    LED_PWM_RED.duty_u16(int((1-c.red)*PWM_DUTY_MAX))
    LED_PWM_GREEN.duty_u16(int((1-c.green)*PWM_DUTY_MAX))
    LED_PWM_BLUE.duty_u16(int((1-c.blue)*PWM_DUTY_MAX))

# Update color variables
def change_color(new_color: color.Color, blink_freq: float = 0, fade_duration: float | None = None) -> None:
    # Update previous and current colors
    globals.PREVIOUS_COLOR = globals.CURRENT_COLOR
    globals.TARGET_COLOR   = new_color

    # Set the time of change
    globals.COLOR_CHANGE_TIME = time.ticks_cpu()

    # Update blink frequency
    globals.BLINK_STATE = False
    globals.BLINK_FREQUENCY = blink_freq
    # if (blink_freq != 0):
    #     print("[Color thread] Blinking at frequency", blink_freq)
    if (fade_duration != None):
        globals.FADE_DURATION = fade_duration

# Initialize variables required for color thread (and other threads relying on color thread)
def color_thread_init() -> None:
    # Initialize colors
    globals.COLOR_MAPPING = {
        "red":    color.Color(1, 0,    0),
        "green":  color.Color(0, 1,    0),
        "blue":   color.Color(0, 0,    1),
        "yellow": color.Color(1, 0.75, 0),
        "purple": color.Color(1, 0,    1),
        "black":  color.Color(0, 0,    0)
    }
    globals.CURRENT_COLOR  = globals.COLOR_MAPPING["black"]
    globals.TARGET_COLOR   = globals.COLOR_MAPPING["black"]
    globals.PREVIOUS_COLOR = globals.COLOR_MAPPING["black"]
    globals.COLOR_CHANGE_TIME  = time.ticks_cpu()

    # Initialize thread variables
    globals.BLINK_STATE = False
    globals.PROGRAM_EXIT = False

    # The following variables are overridden in main.py, as they are read from the config file
    globals.BLINK_FREQUENCY = 0
    globals.FADE_DURATION   = 1
    globals.MAX_BRIGHTNESS  = 1

# Function to be run as color thread
def color_thread() -> None:
    # Start thread
    fade_factor: float = 0
    should_blink: float = True
    while not globals.PROGRAM_EXIT:
        # Get current time and time since last color change (in microseconds)
        t: float = float(time.ticks_cpu())
        dt: float = time.ticks_diff(int(t), globals.COLOR_CHANGE_TIME)
        
        # Rescale time to seconds
        t = pow(10, -6) * t
        dt = pow(10, -6) * dt
        
        # Blink when blink should occur
        should_blink = not (math.floor(2*dt*globals.BLINK_FREQUENCY)+1)%2
        if (should_blink and globals.BLINK_FREQUENCY != 0):
            # Update order matters here! Remember, blinks start "off"
            if (globals.BLINK_STATE):
                globals.TARGET_COLOR   = globals.PREVIOUS_COLOR
                globals.PREVIOUS_COLOR = globals.COLOR_MAPPING["black"]
            else:
                globals.PREVIOUS_COLOR = globals.TARGET_COLOR
                globals.TARGET_COLOR   = globals.COLOR_MAPPING["black"]

            globals.COLOR_CHANGE_TIME = time.ticks_cpu()
            globals.BLINK_STATE = not globals.BLINK_STATE

        if (globals.FADE_DURATION == 0):
            globals.CURRENT_COLOR = globals.TARGET_COLOR
            set_rgb(globals.CURRENT_COLOR)
        else:
            fade_factor = -math.cos(min(dt/globals.FADE_DURATION, 1)*math.pi)/2 + 0.5
            globals.CURRENT_COLOR = globals.PREVIOUS_COLOR*(1-fade_factor) + globals.TARGET_COLOR*fade_factor
            set_rgb(globals.CURRENT_COLOR)

    print("[Color thread] Terminating...")
    set_rgb(globals.COLOR_MAPPING["black"])

if __name__ == "__main__":
    print("Running color_thread.py")

    try:
        color_thread_init()
        _thread.start_new_thread(color_thread, ())
        # time.sleep(0.1)
        print(globals.COLOR_MAPPING)

        change_color(globals.COLOR_MAPPING["red"], fade_duration=0.5)
        time.sleep(0.5)
        change_color(globals.COLOR_MAPPING["black"], fade_duration=0.5)
        time.sleep(0.5)
        change_color(globals.COLOR_MAPPING["blue"], fade_duration=0.5, blink_freq=1)
        time.sleep(10)
        
        globals.PROGRAM_EXIT = True
    except KeyboardInterrupt:
        globals.PROGRAM_EXIT = True

