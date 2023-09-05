# import machine
import urequests
# import network
import time
import _thread
import ujson
import math

# Support files
import color_thread
import globals

# Constants local to this file
# SUCCESS_SYMBOL = "\u2713" # Sometimes displays weird in terminal
SUCCESS_SYMBOL: str = "[O]"
FAILURE_SYMBOL: str = "[X]"
TARGET_BLINK_FREQUENCY: int = 0 # Should be grabbed from config.json

# https://github.com/micropython/micropython-lib/issues/200
# import gc
def retrieve_url(url: str) -> urequests.Response | None:
    # gc.collect()

    try:
        response: urequests.Response = urequests.get(url, timeout=20, headers={"Connection": "close"})

        # print(response.text)
        if (response.status_code != 200):
            raise Exception("Response not OK")
        if (response.text != None and "Web Authentication Redirect" in response.text):
            raise Exception("Redirected to login portal")
        
        return response
    except Exception as exception:
        print(f"{FAILURE_SYMBOL} API call to {url} failed:", exception)
    
    # gc.collect()
    return None

# Connect to WLAN
def connect_wlan() -> bool:
    # Get a list of all available networks
    print("Scanning for available networks...")
    available_networks: list[tuple[bytes, bytes, int, int, int, int]] = globals.WLAN_OBJECT.scan()
    if (len(available_networks) == 0):
        print(f"{FAILURE_SYMBOL} No networks found")
        return False
    
    # Check if any of the available networks are in the config
    union: list[int] = []
    for item in available_networks:
        network_name: str = item[0].decode("utf-8")
        if (network_name in globals.NETWORK_NAMES):
            print(f"- Scan revealed known network: {network_name}")
            priority = get_network_priority_from_name(network_name)
            if (priority != -1):
                union.append(priority)
    
    # If scan revealed no known networks, return false
    if (len(union) == 0):
        print(f"{FAILURE_SYMBOL} No known networks found")
        return False

    # Loop through the available networks in the config, sorted by priority
    for item in sorted(union):
        # Connect to network
        network_name:     str = globals.NETWORKS[item]["ssid"]
        network_password: str = globals.NETWORKS[item]["password"]
        wlan_timeout:     int = globals.NETWORKS[item]["wlan_timeout"]
        globals.WLAN_OBJECT.connect(network_name, network_password)

        # Wait for connection
        print(f"\nAttempting connection to network \"{network_name}\"...")
        timed_out: bool = not wait(wlan_timeout, exit_condition=lambda: globals.WLAN_OBJECT.isconnected(), string="for connection") # Returns true if exit condition met
        if (timed_out):
            print(f"{FAILURE_SYMBOL} Connection timed out")
            continue
        clear_terminal_line()
        print(f"{SUCCESS_SYMBOL} Connected to network:", globals.WLAN_OBJECT.ifconfig()[0])

        # Attempt login if not connected to internet and login portal URL and body provided
        connected: bool = test_connectivity()
        if (not connected):
            print(f"{FAILURE_SYMBOL} Not connected to internet")
            if ("login_portal_url" not in globals.NETWORKS[item] or "login_portal_body" not in globals.NETWORKS[item]):
                print(f"{FAILURE_SYMBOL} No login portal URL or body provided")
                return False

            login_portal_url  = globals.NETWORKS[item]["login_portal_url"]
            login_portal_body = globals.NETWORKS[item]["login_portal_body"]

            print("Attempting \"login\"...")
            res = urequests.post(login_portal_url, data=login_portal_body)
            if ("Connection Successful" in res.text):
                print(f"{SUCCESS_SYMBOL} \"Login\" successful")
            else:
                print("\"Login\" failed")
                return False
        
        print(f"{SUCCESS_SYMBOL} Connected to internet")
        return True

    return False

# Test if the router has internet connection
def test_connectivity() -> bool:
    print("\nChecking internet connection...")
    color_thread.change_color(globals.COLOR_PINGING)

    response: urequests.Response | None = retrieve_url(globals.PING_URL)
    if (response == None):
        return False
    return True

# True represents exit condition met, False represents timeout
def wait(total_ms: int, exit_condition=None, string:str="") -> bool:
    exit_condition_met: bool = False

    milliseconds: int = 0
    while milliseconds < total_ms:
        # Premature exit condition, can be defined as function or lambda
        if (exit_condition != None and exit_condition()):
            exit_condition_met = True
            break

        # Waiting text
        if (milliseconds % 1000 == 0):
            clear_terminal_line()
            print("Waiting", (total_ms-milliseconds)/1000, "s", end="")
            if (string != ""):
                print("", string, end="")
            print("...", end="")

        time.sleep_ms(100)
        milliseconds += 100
    
    # Clear line
    clear_terminal_line()
    return exit_condition_met

# Utility functions
def clear_terminal_line() -> None:
    print("\033[2K\r", end="")
def get_network_priority_from_name(network_name: str) -> int:
    for item in sorted(globals.NETWORKS.keys()):
        if (globals.NETWORKS[item]["ssid"] == network_name):
            return item
    return -1
def api_frequency() -> int:
    if (globals.DOOR_OPEN and globals.DOOR_STATUS_TIME < 60):
        return globals.DOOR_STATUS_TIME * 1000
    return globals.API_INTERVAL
def recent_open_brightness(door_open_time: int) -> float:
    # Interactive demo:
    # https://www.desmos.com/calculator/ipkbhu6orm
    
    # Configurable constants
    END_BRIGHTNESS = globals.MAX_BRIGHTNESS
    START_BRIGHTNESS = 0
    TIME_CONSTANTS = 5 # (1-e^-n) of the end brightness (n=5 => 99.3%)
    TIME_DURATION = 60 # Number of seconds to reach the end brightness

    if (door_open_time > TIME_DURATION):
        return END_BRIGHTNESS
    
    # Don't change anything below this line
    SLOPE = -1/TIME_DURATION * math.log((END_BRIGHTNESS * math.exp(-TIME_CONSTANTS)) / (END_BRIGHTNESS - START_BRIGHTNESS))
    return END_BRIGHTNESS - (END_BRIGHTNESS - START_BRIGHTNESS) * math.exp(-SLOPE * door_open_time)

# Initialization
def initialize_main() -> None:
    # Load config
    with (open("config.json", "rb")) as f:
        config: dict = ujson.loads(f.read())

        # Network stuff
        globals.NETWORKS = config["networks"]
        globals.NETWORK_NAMES = [globals.NETWORKS[item]["ssid"] for item in sorted(globals.NETWORKS.keys())]
        globals.PING_URL = config["ping_url"]
        
        # API stuff
        globals.API_URL  = config["api_url"]
        globals.API_INTERVAL = config["api_interval"]

        # Color stuff
        globals.FADE_DURATION  = float(config["color_fade_duration"])
        TARGET_BLINK_FREQUENCY = float(min(config["color_blink_frequency"], globals.FADE_DURATION/2))
        globals.BLINK_FREQUENCY= TARGET_BLINK_FREQUENCY
        globals.BLINK_STATE    = False
        globals.MAX_BRIGHTNESS = float(config["color_brightness"])

        # Colors
        globals.COLOR_DOOR_OPEN       = globals.COLOR_MAPPING[config["color_mapping"]["door_open"]]
        globals.COLOR_DOOR_CLOSED     = globals.COLOR_MAPPING[config["color_mapping"]["door_closed"]]
        globals.COLOR_API_FAIL        = globals.COLOR_MAPPING[config["color_mapping"]["api_fail"]]
        globals.COLOR_WLAN_CONNECTING = globals.COLOR_MAPPING[config["color_mapping"]["wlan_connecting"]]
        globals.COLOR_PINGING         = globals.COLOR_MAPPING[config["color_mapping"]["pinging"]]

    # WLAN
    # globals.WLAN_OBJECT = network.WLAN(network.STA_IF)
    globals.WLAN_OBJECT.active(True)

    # General
    globals.PROGRAM_EXIT = False

# Main "thread"
def main_thread():
    # Set onboard LED to on
    globals.ONBOARD_LED_PIN.value(1)

    # Connect to WLAN
    color_thread.change_color(globals.COLOR_WLAN_CONNECTING)
    internet_connected: bool = connect_wlan()
    while not internet_connected:
        # print("\nX Failed to connect to internet")
        wait(3000, string="before retrying")
        print("")
        color_thread.change_color(globals.COLOR_WLAN_CONNECTING, blink_freq=TARGET_BLINK_FREQUENCY)
        internet_connected = connect_wlan()
    print("")

    # Loop
    while True:
        print("Calling API...")
        response: urequests.Response | None = retrieve_url(globals.API_URL)
        if (response == None):
            print(f"{FAILURE_SYMBOL} API call failed")

            color_thread.change_color(globals.COLOR_API_FAIL, blink_freq=TARGET_BLINK_FREQUENCY)
            if (not test_connectivity()):
                print(f"{FAILURE_SYMBOL} Lost connection to network, attempting to reconnect...")
                color_thread.change_color(globals.COLOR_WLAN_CONNECTING, blink_freq=TARGET_BLINK_FREQUENCY)
                network_connected: bool = connect_wlan()
                if (network_connected):
                    print(f"{SUCCESS_SYMBOL} Reconnected to network")
                else:
                    print(f"{FAILURE_SYMBOL} Failed to reconnect to network")
                    
            else:
                print(f"{SUCCESS_SYMBOL} Connection to network OK")
            print("")
            # continue
        else:
            try:
                response_json = response.json()
                if (response_json == None):
                    raise Exception("Response JSON is None")
                globals.DOOR_OPEN = bool(int(response_json["open"]))
                globals.DOOR_STATUS_TIME = int(response_json["time"])
                
                # Door is open
                if (globals.DOOR_OPEN):
                    desired_brightness = recent_open_brightness(globals.DOOR_STATUS_TIME)
                    color_thread.change_color(globals.COLOR_DOOR_OPEN * desired_brightness)
                    print("- Door OPEN", end="")
                
                # Door is closed
                else:
                    color_thread.change_color(globals.COLOR_DOOR_CLOSED)
                    print("- Door CLOSED", end="")
                print(" for " + str(globals.DOOR_STATUS_TIME) + " seconds\n")

            except Exception as exception:
                print(f"{FAILURE_SYMBOL} Failed to parse response as JSON: ", exception)
                # continue
        
        # Wait until next api call
        wait_time = api_frequency()
        wait(wait_time, string="until next API call")

if (__name__ == "__main__"):
    # Perform initialization
    initialize_main()

    # Start color thread (only one thread can run at a time) and run main thread
    print("Starting color thread...")
    _thread.start_new_thread(color_thread.color_thread, ())

    try:
        print("Starting main thread...\n")
        main_thread()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt, exiting...")
        clear_terminal_line()
        globals.PROGRAM_EXIT = True
        globals.ONBOARD_LED_PIN.value(0)
