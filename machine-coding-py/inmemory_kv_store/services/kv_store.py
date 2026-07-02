import threading, time
from typing import Generic, Hashable, TypeVar, Optional
from models.entry import Entry
from strategies.lru import LRU

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")

class KVStore(Generic[K, V]):
    def __init__(self, capacity = 2, eviction = None):
        self.cap = capacity
        self.data: dict[K, Entry[V]] = {}
        self.lock = threading.Lock()
        self.eviction = eviction if eviction is not None else LRU()

    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        with self.lock:
            if key not in self.data and len(self.data) >= self.cap:
                self.eviction.evict(self.data)
            exp = time.time() + ttl if ttl else None
            self.data[key] = Entry(value, exp)
            self.eviction.touch(key)

    def get(self, key: K) -> Optional[V]:
        with self.lock:
            entry = self.data.get(key)
            if entry is None:
                return None
            if entry.expiry and entry.expiry < time.time():
                self.delete(key)
                return None
            self.eviction.touch(key)
            return entry.value

    def delete(self, key: K):
        self.data.pop(key, None)
        self.eviction.remove(key)
