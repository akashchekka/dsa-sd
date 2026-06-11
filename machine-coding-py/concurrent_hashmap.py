import threading
from typing import Any, Optional

# 1. Linked List Node for Collision Chaining
class HashNode:
    def __init__(self, key: Any, value: Any):
        self.key = key
        self.value = value
        self.next: Optional['HashNode'] = None

# 2. Thread-Safe Hash Map using Lock Striping
class ConcurrentHashMap:
    def __init__(self, capacity: int = 128, concurrency_level: int = 16):
        self.capacity = capacity
        self.concurrency_level = concurrency_level
        
        # The underlying array of Linked Lists (Buckets)
        self.buckets = [None] * self.capacity
        
        # Array of locks (Lock Striping)
        self.locks =[threading.Lock() for _ in range(self.concurrency_level)]

    def _get_hash(self, key: Any) -> int:
        return hash(key) % self.capacity

    def _get_lock(self, hash_index: int) -> threading.Lock:
        """Maps a bucket index to its respective segment lock."""
        lock_index = hash_index % self.concurrency_level
        return self.locks[lock_index]

    def put(self, key: Any, value: Any):
        index = self._get_hash(key)
        lock = self._get_lock(index)
        
        # Only lock the specific segment, allowing high concurrency!
        with lock:
            node = self.buckets[index]
            if node is None:
                self.buckets[index] = HashNode(key, value)
                return
            
            # Traverse the chain to update or append
            prev = None
            while node:
                if node.key == key:
                    node.value = value  # Update existing
                    return
                prev = node
                node = node.next
            prev.next = HashNode(key, value) # Append to end of chain

    def get(self, key: Any) -> Any:
        index = self._get_hash(key)
        lock = self._get_lock(index)
        
        with lock:
            node = self.buckets[index]
            while node:
                if node.key == key:
                    return node.value
                node = node.next
            raise KeyError(f"Key {key} not found")