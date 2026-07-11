from abc import ABC, abstractmethod

class SchedulingStrategy(ABC):
    @abstractmethod
    def select_elevator(self, elevators, request): ...
