from enum import Enum

class Direction(Enum):
    UP = "UP"
    DOWN = "DOWN"
    IDLE = "IDLE"

class RequestType(Enum):
    PICKUP_UP = "PICKUP_UP"      # hall call: someone wants to go UP
    PICKUP_DOWN = "PICKUP_DOWN"  # hall call: someone wants to go DOWN
    DESTINATION = "DESTINATION"  # in-cabin: passenger picked a floor
