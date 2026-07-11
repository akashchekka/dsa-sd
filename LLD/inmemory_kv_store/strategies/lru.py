from collections import OrderedDict

class LRU:
    def __init__(self):
        self._recency = OrderedDict()

    def touch(self, k):
        if k in self._recency:
            self._recency.move_to_end(k)
        else:
            self._recency[k] = None

    def evict(self, data):
        k, _ = self._recency.popitem(last=False)
        data.pop(k, None)
        return k

    def remove(self, k):
        self._recency.pop(k, None)
