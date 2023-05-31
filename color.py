import machine
import time
import math
import _thread

PWM_DUTY_MAX: int = 2**16-1
PWM_FREQ: int = 100000

RGB_PIN_RED:   machine.Pin = machine.Pin("GP28", machine.Pin.OUT)
RGB_PIN_GREEN: machine.Pin = machine.Pin("GP27", machine.Pin.OUT)
RGB_PIN_BLUE:  machine.Pin = machine.Pin("GP26", machine.Pin.OUT)

RGB_PWM_RED:   machine.PWM = machine.PWM(RGB_PIN_RED)
RGB_PWM_GREEN: machine.PWM = machine.PWM(RGB_PIN_GREEN)
RGB_PWM_BLUE:  machine.PWM = machine.PWM(RGB_PIN_BLUE)

RGB_PWM_RED.freq(PWM_FREQ)
RGB_PWM_GREEN.freq(PWM_FREQ)
RGB_PWM_BLUE.freq(PWM_FREQ)

def init():    
    global color_thread_exit

    color_thread_exit = False

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
            self.name
        )

        return color

    def __sub__(self, rhs):
        color: Color = Color(
            self.red - rhs.red,
            self.green - rhs.green,
            self.blue - rhs.blue,
            self.name
        )

        return color

    def __mul__(self, rhs: float):
        color: Color = Color(
            self.red * rhs,
            self.green * rhs,
            self.blue * rhs,
            self.name
        )

        return color   

    def __rmul__(self, lhs):
        return self.__mul__(lhs)

    def __truediv__(self, rhs: float):
        color: Color = Color(
            self.red / rhs,
            self.green / rhs,
            self.blue / rhs,
            self.name
        )

        return color

    def __rtruediv__(self, lhs):
        return self.__truediv__(lhs)

RED:    Color = Color(1, 0,    0, "red")
GREEN:  Color = Color(0, 1,    0, "green")
BLUE:   Color = Color(0, 0,    1, "blue")
YELLOW: Color = Color(1, 0.75, 0, "yellow")
BLACK:  Color = Color(0, 0,    0, "black")

global_colors: dict[str, Color] = {
    "red":    RED,
    "green":  GREEN,
    "blue":   BLUE,
    "yellow": YELLOW,
    "black":  BLACK
}

global_display_color: Color = BLACK
global_display_color_prev: Color = BLACK
global_color: Color = BLACK
global_color_prev: Color = BLACK

global_blink_freq: float = 0
global_fade_time: float = 1
global_change_time: int = time.ticks_cpu()
global_brightness: float = 1
color_thread_exit: bool = False

# Update RGB LED
def set_rgb(c: Color) -> None:
    c *= global_brightness
    RGB_PWM_RED.duty_u16(int((1-c.red)*PWM_DUTY_MAX))
    RGB_PWM_GREEN.duty_u16(int((1-c.green)*PWM_DUTY_MAX))
    RGB_PWM_BLUE.duty_u16(int((1-c.blue)*PWM_DUTY_MAX))

# Update color variables
def change_color(c: Color, blink_freq: float = 0, fade_time: float | None = None) -> None:
    global global_color, global_color_prev
    global global_display_color, global_display_color_prev
    global global_blink_freq, global_fade_time, global_change_time

    global_color_prev  = global_color
    global_color       = c

    global_display_color = c
    global_display_color_prev = global_color_prev

    global_change_time = time.ticks_cpu()

    global_blink_freq = blink_freq
    if (fade_time != None):
        global_fade_time  = fade_time

def color_thread() -> None:
    global global_color, global_color_prev
    global global_display_color, global_display_color_prev
    global global_blink_freq, global_fade_time, color_thread_exit, global_change_time

    fade_factor: float = 0
    new_blink_value: bool = True
    old_blink_value: bool = True
    while not color_thread_exit:
        t: float = float(time.ticks_cpu())
        dt: float = time.ticks_diff(int(t), global_change_time)
        
        # Rescale time to seconds
        t = pow(10, -6) * t
        dt = pow(10, -6) * dt
        
        old_blink_value = new_blink_value
        new_blink_value = bool((math.floor(t*2*global_blink_freq)+1)%2) # Initialized to True
        
        if (new_blink_value != old_blink_value and global_blink_freq != 0):
            global_change_time = time.ticks_cpu()
            global_display_color_prev = global_display_color
            global_display_color = [BLACK, global_color][new_blink_value]

        if (global_fade_time == 0):
            set_rgb(global_display_color * new_blink_value)
        else:
            fade_factor = -math.cos(min(dt/global_fade_time, 1)*math.pi)/2 + 0.5
            new_color: Color = global_display_color_prev*(1-fade_factor) + global_display_color*fade_factor
            set_rgb(new_color)

    print("[Color thread] Terminating...")
    set_rgb(BLACK)

if __name__ == "__main__":
    try:
        init()

        _thread.start_new_thread(color_thread, ())

        change_color(RED, fade_time=0.5)
        time.sleep(0.5)
        change_color(BLACK, fade_time=0.5)
        time.sleep(0.5)
        change_color(BLUE, fade_time=0.5, blink_freq=1)
        time.sleep(10)
        
        color_thread_exit = True
    except KeyboardInterrupt:
        color_thread_exit = True

