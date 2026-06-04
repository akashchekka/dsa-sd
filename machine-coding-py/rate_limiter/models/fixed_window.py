from threading import Lock


class FixedWindow:

    def __init__(self):
        self.window_start = 0
        self.request_count = 0
        self.lock = Lock()
