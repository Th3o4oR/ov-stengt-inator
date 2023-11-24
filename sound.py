import machine
import time

SPEAKER_PIN: machine.Pin = machine.Pin("GP22", machine.Pin.OUT)
SPEAKER_PWM: machine.PWM = machine.PWM(SPEAKER_PIN)

SPEAKER_DEFAULT_FREQ: int = 1000
PWM_DUTY_MAX: int = 2**16-1
PWM_DUTY_HALF: int = PWM_DUTY_MAX // 2

def beep(num: int = 1, freq: int = SPEAKER_DEFAULT_FREQ, duration: int = 500, pause: int = 500) -> None:
    SPEAKER_PWM.freq(freq)

    for _ in range(num):
        print(f"Beep (frequency: {freq}, duration: {duration}, pause: {pause})")
        SPEAKER_PWM.duty_u16(PWM_DUTY_HALF)
        time.sleep_ms(duration)
        SPEAKER_PWM.duty_u16(0)
        time.sleep_ms(pause)

def play_file(file: str) -> None:
    with open(file, "r") as f:
        lines = f.read()

    lines = lines.split("\n")

    for line in lines:
        line = line.strip()
        line = line.split(" ")
        beep(1, int(line[0]), int(line[1]), int(line[2]))