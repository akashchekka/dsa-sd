from collections import deque
from threading import Lock


class SlidingWindow:

    def __init__(self):
        self.timestamps = deque()
        self.lock = Lock()
