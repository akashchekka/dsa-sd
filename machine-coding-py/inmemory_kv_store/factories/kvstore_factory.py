from enums.eviction_policy import EvictionPolicy
from services.kv_store import KVStore
from strategies.lru import LRU
from strategies.lfu import LFU

class KVStoreFactory:
    _strategies = {
        EvictionPolicy.LRU: LRU,
        EvictionPolicy.LFU: LFU,
    }

    @staticmethod
    def create(capacity=2, policy=EvictionPolicy.LRU):
        strategy_cls = KVStoreFactory._strategies.get(policy)
        if strategy_cls is None:
            raise ValueError(f"Unsupported eviction policy: {policy}")
        return KVStore(capacity, strategy_cls())
