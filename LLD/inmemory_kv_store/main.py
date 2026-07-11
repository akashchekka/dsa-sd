from factories.kvstore_factory import KVStoreFactory
from enums.eviction_policy import EvictionPolicy

s = KVStoreFactory.create(2, EvictionPolicy.LRU)

s.put("a",1)
s.put("b",2)
print(s.get("a"))
s.put("c",3)
print(s.get("b"))
