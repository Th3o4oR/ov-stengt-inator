import machine
import urequests
import network
import time
import _thread
import ujson

# Support files
import color

# Load config
with (open("config.json", "rb")) as f:
    config: dict = ujson.loads(f.read())

    NETWORK_SSID:     str = config["network_ssid"]
    NETWORK_PASSWORD: str = config["network_password"]
    WLAN_TIMEOUT:     int = config["wlan_timeout"]
    PING_URL:         str = config["ping_url"]

    NETWORK_LOGIN_URL:  str = config["login_request_url"]
    NETWORK_LOGIN_BODY: str = config["login_request_body"]

    API_URL:      str = config["api_url"]
    API_INTERVAL: int = config["api_interval"]

    FADE_DURATION: float = float(config["color_fade_duration"])
    BLINK_FREQUENCY: float = float(min(config["color_blink_frequency"], FADE_DURATION/2))

ONBOARD_LED_PIN: machine.Pin = machine.Pin("LED", machine.Pin.OUT)

wlan: network.WLAN
def connect_wlan():
    global wlan

    # Connect to network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(NETWORK_SSID, NETWORK_PASSWORD)
    print("Connecting to network...")

    # Wait for connection
    timed_out: bool = not wait(WLAN_TIMEOUT, exit_condition=lambda: wlan.isconnected(), string="for connection")
    if (timed_out):
        print("X Connection timed out")
        return False
    clear_terminal_line()
    print("√ Connected to network:", wlan.ifconfig()[0])

    # Attempt login to NTNU Guest network
    connected: bool = test_connectivity()
    if (not connected):
        print("Attempting \"login\"...")
        res = urequests.post(NETWORK_LOGIN_URL, data=NETWORK_LOGIN_BODY)
        if ("Connection Successful" in res.text):
            print("√ \"Login\" successful")
        else:
            print("\"Login\" failed")
            return False
    
    print("√ Connected to internet")
    return True

def test_connectivity() -> bool:
    print("\nChecking internet connection...")
    try:
        res = urequests.get(PING_URL)
        if ("Web Authentication Redirect" in res.text or res.status_code != 200):
            raise Exception("No internet connection")
        return True
    except Exception as e:
        print("X Internet connection failed:", e)
        return False

def call_api():
    print("Calling API...")
    try:
        res = urequests.get(API_URL)
        # print(res.text)
        return res
    except Exception as e:
        print("X API call failed:", e)
        return None

# True represents exit condition met, False represents timeout
def wait(total_seconds: int, exit_condition=None, string:str="") -> bool:
    exit_condition_met: bool = False

    seconds: int = 0
    while seconds < total_seconds:
        # Premature exit condition, can be defined as function or lambda
        if (exit_condition != None and exit_condition()):
            exit_condition_met = True
            break

        # Waiting text
        print("\rWaiting", total_seconds - seconds, "seconds", end="")
        if (string != ""):
            print("", string, end="")
        print("...", end="")
        time.sleep(1)
        seconds += 1
    
    # Clear line
    clear_terminal_line()
    return exit_condition_met

def clear_terminal_line() -> None:
    print("\033[2K\r", end="")

def __main__():
    # Set onboard LED to on
    ONBOARD_LED_PIN.value(1)
    
    color.change_color(color.BLUE, fade_time=FADE_DURATION)
    internet_connected: bool = connect_wlan()
    while not internet_connected:
        print("X Failed to connect to internet, retrying...")
        color.change_color(color.BLUE, fade_time=FADE_DURATION, blink_freq=BLINK_FREQUENCY)
        internet_connected = connect_wlan()
    print("")

    while True:
        response: str | None = call_api()
        if (response == None):
            color.change_color(color.YELLOW, fade_time=FADE_DURATION, blink_freq=BLINK_FREQUENCY)
            if (not test_connectivity()):
                print("X Lost connection to network, attempting to reconnect...")
                color.change_color(color.BLUE, fade_time=FADE_DURATION, blink_freq=BLINK_FREQUENCY)
                network_connected: bool = connect_wlan()
                if (network_connected):
                    print("√ Reconnected to network")
                else:
                    print("X Failed to reconnect to network")
                    
            else:
                print("√ Connection to network OK")
            print("")
            # continue
        else:
            response_json = response.json()
            if (response_json["open"] == "1"):
                color.change_color(color.GREEN, fade_time=FADE_DURATION)
                print("Door OPEN", end="")
            else:
                color.change_color(color.RED, fade_time=FADE_DURATION)
                print("Door CLOSED", end="")
            print(" for " + str(response_json["time"]) + " seconds\n")
        
        # Wait until next api call
        wait(API_INTERVAL, string="until next API call")

try:
    color.init()
    _thread.start_new_thread(color.color_thread, ())
    __main__()
except KeyboardInterrupt:
    print("\nKeyboard interrupt, exiting...")
    clear_terminal_line()
    color.color_thread_exit = True
    # time.sleep(0.1)
    ONBOARD_LED_PIN.value(0)
