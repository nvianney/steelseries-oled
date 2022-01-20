import platform
import json
from os import path
import requests
from threading import Thread
from threading import Event
from time import sleep
import traceback
from collections import deque

# user defined variables
DISPLAY_NAME = "test game name"
DEVELOPER_NAME = "rimooneystudios"

# developer variables. can break the program
HEARTBEAT = 10
GAME_NAME = "PYTHON_TEST"
STEELSERIES_JSON_FILE = "%PROGRAMDATA%/SteelSeries/SteelSeries Engine 3/coreProps.json"
LINES_EVENT = "LINES"

class Client:
    '''
    A client-server interface. API endpoints are implemented according to
    https://github.com/SteelSeries/gamesense-sdk/blob/master/doc/api/sending-game-events.md

    The server accepts HTTP POST requests.

    In order to keep the connection active, SteelSeries requires a heartbeat request every
    15 seconds (configurable). The heartbeat() method will send this heartbeat. It is up
    to the user to implement code that will automaticaly call this method.
    '''
    def __init__(self, address):
        self.address = address

    def post(self, endpoint, data):
        '''
        sends an HTTP POST request to the specified endpoint with the given json data

            parameters:
                endpoint:   the HTTP endpoint
                data:       JSON data
            
            returns:
                True if response is 200, False otherwise
        '''
        r = requests.post(self.address + endpoint, json=data)
        if r.status_code != 200:
            print(f"Error: request of {endpoint} returned a status of {r.status_code}")
            print(f"Response body:\n{r.text}")
            print("Stack trace:")
            for line in traceback.format_stack():
                print(line.strip())
            return False
        return True
    
    def registerGame(self):
        '''
        Performs initialization with the user defined parameters.
        '''
        data = {
            "game": GAME_NAME,
            "game_display_name": DISPLAY_NAME,
            "developer": DEVELOPER_NAME
        }
        return self.post("/game_metadata", data)

    def bindEvent(self, data):
        '''
        Performs a POST request to /bind_game_event with the specified data.
        '''
        return self.post("/bind_game_event", data)

    def sendEvent(self, data):
        '''
        Performs a POST request to /game_event with the specified data.
        '''
        return self.post("/game_event", data)
    
    def heartbeat(self):
        '''
        Sends a heartbeat request to /game_heartbeat.
        '''
        data = {
            "game": GAME_NAME
        }
        return self.post("/game_heartbeat", data)

# ---------------------------

class Heartbeat:
    '''
    Heartbeat instance that spawns another separate thread to continually call heartbeat()
    every HEARTBEAT seconds.
    '''

    def __init__(self, client, delay):
        self.client = client
        self.delay = delay
        self.active = False
    
    def start(self):
        '''
        Starts the heartbeat thread.
        '''
        if self.active:
            print("Heartbeat is already running")
            return

        self.active = True
        self.e = Event()

        # Spawn new thread
        self.thread = Thread(target = self.func)
        self.thread.start()

    def func(self):
        while self.active:
            self.client.heartbeat()
            # wait for self.delay seconds or be interrupted, whatever is first
            self.e.wait(timeout = self.delay)

    def stop(self, block = True):
        '''
        Stops the heartbeat thread.

            parameters:
                block: set to True to block the main thread. False to stop asynchronously.
        '''
        if not self.active:
            print("Heartbeat hasn't been running")
            return False
        
        self.active = False
        self.e.set()

        # block main thread until heartbeat is dead
        if block:
            self.thread.join()

_client = None

def connect():
    # Only works on windows for now
    if platform.system().lower() != "windows":
        print("Program only works on Windows.")
        exit(1)
    
    # Check if the program is running https://github.com/SteelSeries/gamesense-sdk/blob/master/doc/api/sending-game-events.md#server-discovery
    jsonFile = path.expandvars(STEELSERIES_JSON_FILE)
    if not path.isfile(jsonFile):
        print("SteelSeries Engine 3 isn't running")
        exit(1)

    f = open(path.expandvars(STEELSERIES_JSON_FILE))
    data = json.load(f)

    addr = data["address"]
    client = Client("http://" + addr)


    result = client.registerGame()
    if not result:
        print("Unknown error")
        exit(1)

    data = {
        "game": GAME_NAME,
        "event": LINES_EVENT,
        "min_value": 0,
        "max_value": 100,
        "icon_id": 1,
        "handlers": [
            {
                "device-type": "screened",
                "zone": "one",
                "mode": "screen",
                "value_optional": True,
                "datas": [
                    {
                        "lines": [
                            {
                                "has-text": True,
                                "context-frame-key": "custom-text-1"
                            },
                            {
                                "has-text": True,
                                "context-frame-key": "custom-text-2"
                            },
                            {
                                "has-text": True,
                                "context-frame-key": "custom-text-3"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    _client.bindEvent(data)


    # Begin heartbeat on a separate thread to notify the server every x seconds
    global _heartbeat
    _heartbeat = Heartbeat(client, HEARTBEAT)
    _heartbeat.start()

    global _client
    _client = client


def disconnect():
    _heartbeat.stop()
    global _client
    _client = None

def _main():
    connect()

    # the juicy stuff
    # https://github.com/SteelSeries/gamesense-sdk/blob/master/doc/api/json-handlers-screen.md

    data = {
        "game": GAME_NAME,
        "event": LINES_EVENT,
        "data": {
            "frame": {
                "custom-text-1": "TEST",
                "custom-text-2": "TEST2",
                "custom-text-3": "3TEST"
            }
        }
    }
    _client.sendEvent(data)

    disconnect()


# to make sure it's run by script instead of being imported
if __name__ == "__main__":
    _main()

# private apis

def _verifyActive():
    if _client == None:
        print("Not connected to SteelSeries. Did you call connect()?")
        exit(1)

ROWS = 3
textQueue = deque(maxlen=ROWS)
textQueue.extend([""] * ROWS)

def _writeBuffer():
    data = {
        "game": GAME_NAME,
        "event": LINES_EVENT,
        "data": {
            "frame": {
                "custom-text-1": str(textQueue[0]),
                "custom-text-2": str(textQueue[1]),
                "custom-text-3": str(textQueue[2])
            }
        }
    }
    _client.sendEvent(data)

# publicly exposed APIs
def printText(obj):
    '''
    Prints an object to the OLED screen

        parameters:
            obj: the object to write
    '''

    _verifyActive()

    textQueue.append(str(obj))
    print(textQueue)
    print("Recent: " + str(textQueue[2]))
    
    _writeBuffer()

def clear():
    '''
    Clears all text from the OLED screen
    '''

    _verifyActive()

    textQueue.extend([""] * ROWS)

    _writeBuffer()

def setText(row, string):
    '''
    Sets a text to the OLED screen

        parameters:
            row: the row number to set
            string: the string to set
    '''

    _verifyActive()


    textQueue[row] = str(string)
    
    _writeBuffer()

