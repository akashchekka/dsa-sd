from abc import ABC, abstractmethod

class Eviction(ABC):
    @abstractmethod
    def touch(self, key): ...

    @abstractmethod
    def evict(self, data): ...
