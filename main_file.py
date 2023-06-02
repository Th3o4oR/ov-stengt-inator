import machine
import urequests
import network
import time
import _thread
import ujson

# Support files
import color_thread
import globals

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
        print(f"X API call to {url} failed:", exception)
    
    # gc.collect()
    return None

# Connect to WLAN
def connect_wlan() -> bool:
    # Get a list of all available networks
    print("Scanning for available networks...")
    available_networks: list[tuple[bytes, bytes, int, int, int, int]] = globals.WLAN_OBJECT.scan()
    if (len(available_networks) == 0):
        print("X No networks found")
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

    # Loop through the available networks in the config, sorted by priority
    for item in sorted(union):
        # Connect to network
        network_name:     str = globals.NETWORKS[item]["ssid"]
        network_password: str = globals.NETWORKS[item]["password"]
        wlan_timeout:     int = globals.NETWORKS[item]["wlan_timeout"]
        globals.WLAN_OBJECT.connect(network_name, network_password)

        # Wait for connection
        print(f"Attempting connection to network \"{network_name}\"...")
        timed_out: bool = not wait(wlan_timeout, exit_condition=lambda: globals.WLAN_OBJECT.isconnected(), string="for connection") # Returns true if exit condition met
        if (timed_out):
            print("X Connection timed out")
            continue
        clear_terminal_line()
        print("√ Connected to network:", globals.WLAN_OBJECT.ifconfig()[0])

        # Attempt login if not connected to internet and login portal URL and body provided
        connected: bool = test_connectivity()
        if (not connected):
            print("X Not connected to internet")
            if ("login_portal_url" not in globals.NETWORKS[item] or "login_portal_body" not in globals.NETWORKS[item]):
                print("X No login portal URL or body provided")
                return False

            login_portal_url  = globals.NETWORKS[item]["login_portal_url"]
            login_portal_body = globals.NETWORKS[item]["login_portal_body"]

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

# Test if the router has internet connection
def test_connectivity() -> bool:
    print("\nChecking internet connection...")
    color_thread.change_color(globals.COLOR_PINGING, fade_time=globals.FADE_DURATION)

    response: urequests.Response | None = retrieve_url(globals.PING_URL)
    if (response == None):
        return False
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

# Utility functions
def clear_terminal_line() -> None:
    print("\033[2K\r", end="")
def get_network_priority_from_name(network_name: str) -> int:
    for item in sorted(globals.NETWORKS.keys()):
        if (globals.NETWORKS[item]["ssid"] == network_name):
            return item
    return -1

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
        globals.FADE_DURATION   = float(config["color_fade_duration"])
        globals.BLINK_FREQUENCY = float(min(config["color_blink_frequency"], globals.FADE_DURATION/2))
        globals.BRIGHTNESS      = float(config["color_brightness"])

    # Colors
    globals.COLOR_DOOR_OPEN       = globals.COLOR_MAPPING[config["color_mapping"]["door_open"]]
    globals.COLOR_DOOR_CLOSED     = globals.COLOR_MAPPING[config["color_mapping"]["door_closed"]]
    globals.COLOR_API_FAIL        = globals.COLOR_MAPPING[config["color_mapping"]["api_fail"]]
    globals.COLOR_WLAN_CONNECTING = globals.COLOR_MAPPING[config["color_mapping"]["wlan_connecting"]]
    globals.COLOR_PINGING         = globals.COLOR_MAPPING[config["color_mapping"]["pinging"]]

    # WLAN
    # globals.WLAN_OBJECT = network.WLAN(network.STA_IF)
    globals.WLAN_OBJECT.active(True)

# Main "thread"
def main_thread():
    # Set onboard LED to on
    globals.ONBOARD_LED_PIN.value(1)

    # Connect to WLAN
    color_thread.change_color(globals.COLOR_WLAN_CONNECTING, fade_time=globals.FADE_DURATION)
    internet_connected: bool = connect_wlan()
    while not internet_connected:
        print("\nX Failed to connect to internet")
        wait(3, string="before retrying")
        print("")
        color_thread.change_color(globals.COLOR_WLAN_CONNECTING, fade_time=globals.FADE_DURATION, blink_freq=globals.BLINK_FREQUENCY)
        internet_connected = connect_wlan()
    print("")

    # Loop
    while True:
        # response = retrieve_url(API_URL)
        print("Calling API...")
        response: urequests.Response | None = retrieve_url(globals.API_URL)

        if (response == None):
            print("X API call failed")

            color_thread.change_color(globals.COLOR_API_FAIL, fade_time=globals.FADE_DURATION, blink_freq=globals.BLINK_FREQUENCY)
            if (not test_connectivity()):
                print("X Lost connection to network, attempting to reconnect...")
                color_thread.change_color(globals.COLOR_WLAN_CONNECTING, fade_time=globals.FADE_DURATION, blink_freq=globals.BLINK_FREQUENCY)
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
            try:
                response_json = response.json()
                if (response_json == None):
                    raise Exception("Response JSON is None")
                
                if (response_json["open"] == "1"):
                    color_thread.change_color(globals.COLOR_DOOR_OPEN, fade_time=globals.FADE_DURATION)
                    print("Door OPEN", end="")
                else:
                    color_thread.change_color(globals.COLOR_DOOR_CLOSED, fade_time=globals.FADE_DURATION)
                    print("Door CLOSED", end="")
                print(" for " + str(response_json["time"]) + " seconds\n")

            except Exception as exception:
                print("X Failed to parse response as JSON")
                # print(exception)
                # continue
        
        # Wait until next api call
        wait(globals.API_INTERVAL, string="until next API call")

if (__name__ == "__main__"):
    # Perform initialization
    color_thread.color_thread_init() # Needs to be called before starting thread, to ensure that the thread is not started before all the required variables have been defined
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
        globals.COLOR_THREAD_EXIT = True
        globals.ONBOARD_LED_PIN.value(0)
