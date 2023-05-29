import machine
import urequests
import network
import time
import sys # For exiting
import _thread

# Support files
import credentials
import color

API_URL:  str = "http://www.omegav.no/api/dooropen.php"
# PING_URL: str = "http://google.com" # This causes issues with returned value
PING_URL: str = "http://neverssl.com"
NETWORK_LOGIN_URL:  str = "https://wlc.it.ntnu.no/login.html"
NETWORK_LOGIN_BODY: str = "buttonClicked=4&err_flag=0&info_flag=0&info_msg=0&email=example%40mail.com"

# Times
WLAN_CONNECTION_TIMEOUT: int = 20 # Seconds
API_CALL_INTERVAL:       int = 60 # Seconds

ONBOARD_LED_PIN = machine.Pin("LED", machine.Pin.OUT)

wlan: network.WLAN
def connect_wlan():
    global wlan

    # Connect to network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(credentials.NETWORK_SSID, credentials.NETWORK_PASSWORD)
    print("Connecting to network...")

    # Wait for connection
    timed_out: bool = not wait(WLAN_CONNECTION_TIMEOUT, exit_condition=lambda: wlan.isconnected(), string="for connection")
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
    
    color.change_color(color.BLUE)
    internet_connected: bool = connect_wlan()
    while not internet_connected:
        print("X Failed to connect to internet, retrying...")
        color.change_color(color.BLUE, blink=True)
        internet_connected = connect_wlan()
    print("")

    while True:
        response: str | None = call_api()
        if (response == None):
            color.change_color(color.YELLOW, blink=True)
            if (not test_connectivity()):
                print("X Lost connection to network, attempting to reconnect...")
                color.change_color(color.BLUE, blink=True)
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
                color.change_color(color.GREEN)
                print("Door OPEN", end="")
            else:
                color.change_color(color.RED)
                print("Door CLOSED", end="")
            print(" for " + str(response_json["time"]) + " seconds\n")
        
        # Wait until next api call
        wait(API_CALL_INTERVAL, string="until next API call")

try:
    blink_thread: int = _thread.start_new_thread(color.color_thread, ())
    __main__()
except KeyboardInterrupt:
    clear_terminal_line()
    print("Keyboard interrupt, exiting...")
    color.color_thread_exit = True
    ONBOARD_LED_PIN.value(0)
    sys.exit()
