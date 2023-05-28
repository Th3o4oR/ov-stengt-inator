import machine
import time

RGB_PIN_RED:   machine.Pin = machine.Pin("GP28", machine.Pin.OUT)
RGB_PIN_GREEN: machine.Pin = machine.Pin("GP27", machine.Pin.OUT)
RGB_PIN_BLUE:  machine.Pin = machine.Pin("GP26", machine.Pin.OUT)

RGB_EN:  int = 0
RGB_DIS: int = 1

class Color:
    def __init__(self, r: int, g: int, b: int, name: str):
        self.red = r
        self.green = g
        self.blue = b
        self.name = name
    red: int
    green: int
    blue: int

RED:    Color = Color(RGB_EN,  RGB_DIS, RGB_DIS, "red")
GREEN:  Color = Color(RGB_DIS, RGB_EN,  RGB_DIS, "green")
BLUE:   Color = Color(RGB_DIS, RGB_DIS, RGB_EN,  "blue")
YELLOW: Color = Color(RGB_EN,  RGB_EN,  RGB_DIS, "yellow")
BLACK:  Color = Color(RGB_DIS, RGB_DIS, RGB_DIS, "black")
global_color: Color = BLACK
global_blink: bool = False

# Update RGB LED
def set_rgb(c: Color) -> None:
    RGB_PIN_RED.value(c.red)
    RGB_PIN_GREEN.value(c.green)
    RGB_PIN_BLUE.value(c.blue)

# Update color variables
def change_color(c: Color, blink: bool = False) -> None:
    global global_color, global_blink
    global_color = c
    global_blink = blink

color_thread_exit: bool = False
def color_thread() -> None:
    global global_blink, global_color, color_thread_exit

    color_thread_color: Color = BLACK
    while not color_thread_exit:
        # Update color
        if (global_color != color_thread_color):
            color_thread_color = global_color
            set_rgb(color_thread_color)

        # Blink
        if global_blink:
            set_rgb(color_thread_color)
            time.sleep(1)
            set_rgb(BLACK)
            time.sleep(1)

    print("[Color thread] Terminating...")
    set_rgb(BLACK)
