import machine
import urequests
import network
import time
import _thread
import ujson

# Support files
import color

# Global variables
NETWORKS: dict
PING_URL: str
API_URL: str
API_INTERVAL: int
wlan: network.WLAN

FADE_DURATION: float
BLINK_FREQUENCY: float

COLOR_MAPPING: dict[str, str]
COLOR_DOOR_OPEN: color.Color
COLOR_DOOR_CLOSED: color.Color
COLOR_API_FAIL: color.Color
COLOR_ATTEMPTING_CONNECTION: color.Color
COLOR_CHECKING_INTERNET: color.Color

ONBOARD_LED_PIN: machine.Pin

# Initialization
def __init__():
    global NETWORKS, PING_URL, API_URL, API_INTERVAL, wlan, FADE_DURATION, BLINK_FREQUENCY, COLOR_MAPPING, COLOR_DOOR_OPEN, COLOR_DOOR_CLOSED, COLOR_API_FAIL, COLOR_ATTEMPTING_CONNECTION, COLOR_CHECKING_INTERNET, ONBOARD_LED_PIN

    ONBOARD_LED_PIN: machine.Pin = machine.Pin("LED", machine.Pin.OUT)

    # Load config
    with (open("config.json", "rb")) as f:
        config: dict = ujson.loads(f.read())

        NETWORKS = config["networks"]
        PING_URL = config["ping_url"]
        API_URL  = config["api_url"]
        API_INTERVAL = config["api_interval"]

        FADE_DURATION = float(config["color_fade_duration"])
        BLINK_FREQUENCY = float(min(config["color_blink_frequency"], FADE_DURATION/2))

        COLOR_MAPPING = config["color_mapping"]

    wlan = network.WLAN(network.STA_IF)

    # Colors
    COLOR_DOOR_OPEN             = color.global_colors[COLOR_MAPPING["door_open"]]
    COLOR_DOOR_CLOSED           = color.global_colors[COLOR_MAPPING["door_closed"]]
    COLOR_API_FAIL              = color.global_colors[COLOR_MAPPING["api_fail"]]
    COLOR_ATTEMPTING_CONNECTION = color.global_colors[COLOR_MAPPING["attempting_connection"]]
    COLOR_CHECKING_INTERNET     = color.global_colors[COLOR_MAPPING["checking_internet"]]

    # Connect WLAN
    color.change_color(COLOR_ATTEMPTING_CONNECTION, fade_time=FADE_DURATION)
    internet_connected: bool = connect_wlan()
    while not internet_connected:
        print("\nX Failed to connect to internet")
        wait(3, string="before retrying")
        print("")
        color.change_color(COLOR_ATTEMPTING_CONNECTION, fade_time=FADE_DURATION, blink_freq=BLINK_FREQUENCY)
        internet_connected = connect_wlan()
    print("")

# wlan: network.WLAN = network.WLAN(network.STA_IF)
# if (wlan.isconnected()):
#     wlan.disconnect()
# wlan.active(False)
def connect_wlan() -> bool:
    # global wlan

    for item in sorted(NETWORKS.keys()):
        network_name:     str = NETWORKS[item]["ssid"]
        network_password: str = NETWORKS[item]["password"]
        wlan_timeout:     int = NETWORKS[item]["wlan_timeout"]

        wlan.active(True)
        wlan.connect(network_name, network_password)

        # print(f"Attempting connection to network \"{network_name}\" with password \"{network_password}\"...")
        print(f"Attempting connection to network \"{network_name}\"...")
        timed_out: bool = not wait(wlan_timeout, exit_condition=lambda: wlan.isconnected(), string="for connection") # Returns true if exit condition met
        if (timed_out):
            print("X Connection timed out")
            continue
        clear_terminal_line()
        print("√ Connected to network:", wlan.ifconfig()[0])

        # Attempt login to NTNU Guest network
        connected: bool = test_connectivity()
        if (not connected):
            print("X Not connected to internet")
            if ("login_portal_url" not in NETWORKS[item] or "login_portal_body" not in NETWORKS[item]):
                print("X No login portal URL or body provided")
                return False

            login_portal_url  = NETWORKS[item]["login_portal_url"]
            login_portal_body = NETWORKS[item]["login_portal_body"]

            print("Attempting \"login\"...")
            res = urequests.post(login_portal_url, data=login_portal_body)
            if ("Connection Successful" in res.text):
                print("√ \"Login\" successful")
            else:
                print("\"Login\" failed")
                return False
        
        print("√ Connected to internet")
        return True

    return False

# https://github.com/micropython/micropython-lib/issues/200
# import gc
def retrieve_url(url: str) -> urequests.Response | None:
    # gc.collect()
    response = None

    try:
        response = urequests.get(url, timeout=20)
        print(response.text)
        if (response.status_code != 200):
            raise Exception("Response not OK")
        if ("Web Authentication Redirect" in response.text):
            raise Exception("Redirected to login portal")
        
        return response
    except Exception as e:
        print(f"X API call to {url} failed:", e)
        if (isinstance(e, OSError) and response):
            # print("Caught OSError, closing response")
            response.close()
    
    # gc.collect()
    return response

def test_connectivity() -> bool:
    print("\nChecking internet connection...")
    color.change_color(COLOR_CHECKING_INTERNET, fade_time=FADE_DURATION)

    response: urequests.Response | None = retrieve_url(PING_URL)
    if (response == None):
        color.change_color(color.BLACK, fade_time=FADE_DURATION)
        return False
    color.change_color(color.BLACK, fade_time=FADE_DURATION)
    return True

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
        clear_terminal_line()
        print("Waiting", total_seconds-seconds, "seconds", end="")
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
    # Initialize
    __init__()

    # Set onboard LED to on
    ONBOARD_LED_PIN.value(1)

    # # Colors
    # COLOR_DOOR_OPEN             = color.global_colors[COLOR_MAPPING["door_open"]]
    # COLOR_DOOR_CLOSED           = color.global_colors[COLOR_MAPPING["door_closed"]]
    # COLOR_API_FAIL              = color.global_colors[COLOR_MAPPING["api_fail"]]
    # COLOR_ATTEMPTING_CONNECTION = color.global_colors[COLOR_MAPPING["attempting_connection"]]
    
    # color.change_color(COLOR_ATTEMPTING_CONNECTION, fade_time=FADE_DURATION)
    # internet_connected: bool = connect_wlan()
    # while not internet_connected:
    #     print("\nX Failed to connect to internet")
    #     wait(5, string="before retrying")
    #     print("")
    #     color.change_color(COLOR_ATTEMPTING_CONNECTION, fade_time=FADE_DURATION, blink_freq=BLINK_FREQUENCY)
    #     internet_connected = connect_wlan()
    # print("")

    while True:
        # response = retrieve_url(API_URL)
        print("Calling API...")
        response: urequests.Response | None = retrieve_url(API_URL)

        if (response == None):
            print("X API call failed")

            color.change_color(COLOR_API_FAIL, fade_time=FADE_DURATION, blink_freq=BLINK_FREQUENCY)
            if (not test_connectivity()):
                print("X Lost connection to network, attempting to reconnect...")
                color.change_color(COLOR_ATTEMPTING_CONNECTION, fade_time=FADE_DURATION, blink_freq=BLINK_FREQUENCY)
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
                color.change_color(COLOR_DOOR_OPEN, fade_time=FADE_DURATION)
                print("Door OPEN", end="")
            else:
                color.change_color(COLOR_DOOR_CLOSED, fade_time=FADE_DURATION)
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
