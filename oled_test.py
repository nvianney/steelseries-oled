import platform
import json
from os import path
import requests
from threading import Thread
from threading import Event
from time import sleep

# user defined variables
DISPLAY_NAME = "test game name"
DEVELOPER_NAME = "rimooneystudios"

# developer variables. can break the program
HEARTBEAT = 10
GAME_NAME = "PYTHON_TEST"
STEELSERIES_JSON_FILE = "%PROGRAMDATA%/SteelSeries/SteelSeries Engine 3/coreProps.json"

class Client:
    '''
    client-steelseries server interface. API endpoints are implemented according to
    https://github.com/SteelSeries/gamesense-sdk/blob/master/doc/api/sending-game-events.md
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
            print(f"Error: request of {dict} returned a status of {r.status_code}")
            r.s
            print(f"Response body:\n{r.text}")
            return False
        return True
    
    def registerGame(self):
        data = {
            "game": GAME_NAME,
            "game_display_name": DISPLAY_NAME,
            "developer": DEVELOPER_NAME
        }
        return self.post("/game_metadata", data)

    def bindEvent(self, data):
        return self.post("/bind_game_event", data)

    def sendEvent(self, data):
        return self.post("/game_event", data)
    
    def heartbeat(self):
        data = {
            "game": GAME_NAME
        }
        return self.post("/game_heartbeat", data)

# ---------------------------

class Heartbeat:

    def __init__(self, client):
        self.client = client
        self.active = False
    
    def start(self):
        if self.active:
            print("Heartbeat is already running")
            return

        self.active = True
        self.e = Event()
        self.thread = Thread(target = self.func)
        self.thread.start()

    def func(self):
        while self.active:
            self.client.heartbeat()
            self.e.wait(timeout = HEARTBEAT)

    def stop(self, block):
        if not self.active:
            print("Heartbeat hasn't been running")
            return False
        
        self.active = False
        self.e.set()

        # block main thread until heartbeat is dead
        if block:
            self.thread.join()


def heartbeatThread():
    sleep(HEARTBEAT)

def main():
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
    
    # Begin heartbeat on a separate thread to notify the server every x seconds
    heartbeat = Heartbeat(client)
    heartbeat.start()

    # the juicy stuff
    # https://github.com/SteelSeries/gamesense-sdk/blob/master/doc/api/json-handlers-screen.md
    data = {
        "game": GAME_NAME,
        "event": "EVENT1",
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
                                "context-frame-key": "line 1"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    client.bindEvent(data)

    client.sendEvent("EVENT1")

    sleep(10)

    # kill
    heartbeat.stop()

# to make sure it's run by script instead of being imported
if __name__ == "__main__":
    main()
