from abc import ABC, abstractmethod


class RateLimiter(ABC):

    @abstractmethod
    def allow_request(self, user_id: str) -> bool:
        pass
