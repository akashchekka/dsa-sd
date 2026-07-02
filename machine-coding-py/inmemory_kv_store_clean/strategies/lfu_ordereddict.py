from collections import defaultdict

class LFU:
    def __init__(self):
        self.frequency = defaultdict(int)

    def touch(self, key):
        self.frequency[key] += 1

    def evict(self, data):
        key = min(self.frequency, key=self.frequency.get)
        self.frequency.pop(key, None)
        data.pop(key, None)
        return key

    def remove(self, key):
        self.frequency.pop(key, None)
