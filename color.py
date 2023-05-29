import machine
import time
import math

PWM_DUTY_MAX: int = 2**16-1
PWM_FREQ: int = 1000

RGB_PIN_RED:   machine.Pin = machine.Pin("GP28", machine.Pin.OUT)
RGB_PIN_GREEN: machine.Pin = machine.Pin("GP27", machine.Pin.OUT)
RGB_PIN_BLUE:  machine.Pin = machine.Pin("GP26", machine.Pin.OUT)

RGB_PWM_RED:   machine.PWM = machine.PWM(RGB_PIN_RED)
RGB_PWM_GREEN: machine.PWM = machine.PWM(RGB_PIN_GREEN)
RGB_PWM_BLUE:  machine.PWM = machine.PWM(RGB_PIN_BLUE)

RGB_PWM_RED.freq(PWM_FREQ)
RGB_PWM_GREEN.freq(PWM_FREQ)
RGB_PWM_BLUE.freq(PWM_FREQ)

class Color:
    def __init__(self, r: float, g: float, b: float, name: str):
        self.red: float = r
        self.green: float = g
        self.blue: float = b
        self.name: str = name

    def __add__(self, rhs):
        color: Color = Color(
            self.red + rhs.red,
            self.green + rhs.green,
            self.blue + rhs.blue,
            self.name + " + " + rhs.name
        )

        return color

    def __sub__(self, rhs):
        color: Color = Color(
            self.red - rhs.red,
            self.green - rhs.green,
            self.blue - rhs.blue,
            self.name + " - " + rhs.name
        )

        return color

    def __mul__(self, rhs: float):
        color: Color = Color(
            self.red * rhs,
            self.green * rhs,
            self.blue * rhs,
            self.name + " * " + str(rhs)
        )

        return color
        
    def __truediv__(self, rhs: float):
        color: Color = Color(
            self.red / rhs,
            self.green / rhs,
            self.blue / rhs,
            self.name + " / " + str(rhs)
        )

        return color

RED:    Color = Color(1,    0,    0, "red")
GREEN:  Color = Color(0,    1,    0, "green")
BLUE:   Color = Color(0,    0,    1, "blue")
YELLOW: Color = Color(1,    0.75, 0, "yellow")
BLACK:  Color = Color(0,    0,    0, "black")

BRIGHTNESS = 1

global_color: Color = BLACK
global_prev_color: Color = BLACK
global_blink_freq: float = 0
global_fade_time: float = 1
global_change_time: int = time.ticks_cpu()

# Update RGB LED
def set_rgb(c: Color) -> None:
    RGB_PWM_RED.duty_u16(int((1-c.red)*PWM_DUTY_MAX))
    RGB_PWM_GREEN.duty_u16(int((1-c.green)*PWM_DUTY_MAX))
    RGB_PWM_BLUE.duty_u16(int((1-c.blue)*PWM_DUTY_MAX))

# Update color variables
def change_color(c: Color, blink_freq: float = 0, fade_time: float = 0) -> None:
    global global_color, global_prev_color, global_blink_freq, global_fade_time, global_change_time
    global_prev_color = global_color
    global_color = c
    global_blink_freq = blink_freq
    global_fade_time = fade_time
    global_change_time = time.ticks_cpu()

color_thread_exit: bool = False
def color_thread() -> None:
    global global_color, global_prev_color, global_blink_freq, global_fade_time, color_thread_exit

    while not color_thread_exit:
        t: float = time.ticks_cpu()
        dt: float = time.ticks_diff(t, global_change_time)
        
        t *= 10**-6
        dt *= 10**-6
        
        fade_factor: float = 1.0 if not global_fade_time else (-math.cos(min(dt/global_fade_time, 1)*math.pi)+1)/2
        blink_factor: float = (math.floor(t*2*global_blink_freq)+1)%2

        set_rgb((global_prev_color*(1-fade_factor) + global_color*fade_factor)*blink_factor*BRIGHTNESS)

    print("[Color thread] Terminating...")
    set_rgb(BLACK)