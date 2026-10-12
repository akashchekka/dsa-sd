import hashlib
import bisect

class ConsistentHash:
    def __init__(self, replicas=3):
        self.replicas = replicas
        self.ring = {}       # hash_position -> node
        self.sorted_keys = []

    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    def add_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            self.ring[key] = node

        self.sorted_keys = sorted(self.ring)

    def remove_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f"{node}:{i}")
            del self.ring[key]

        self.sorted_keys = sorted(self.ring)

    def get_node(self, key):
        if not self.ring:
            return None

        hash_value = self._hash(key)

        index = bisect.bisect_right(
            self.sorted_keys,
            hash_value
        )

        if index == len(self.sorted_keys):
            index = 0

        return self.ring[self.sorted_keys[index]]