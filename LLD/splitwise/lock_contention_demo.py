"""Lock contention demo: one global lock (always-lock) vs double-checked locking.

Many threads race to get-or-create the SAME small set of keys. Both versions are
correct (each key created exactly once), but they differ in how often threads
must actually acquire the lock:

- AlwaysLockStore: takes the lock on EVERY call -> every thread serializes here,
  even when the object already exists. High contention.
- DoubleCheckedStore: lock-free fast path; only takes the lock on the rare
  "not created yet" path. Once warm, almost no thread touches the lock.

Run:  python lock_contention_demo.py
"""
from __future__ import annotations

import threading
import time


class AlwaysLockStore:
    """Grabs the lock on every get-or-create call."""

    def __init__(self) -> None:
        self._data: dict[str, object] = {}
        self._lock = threading.Lock()
        self.lock_acquisitions = 0          # how many times we entered the lock

    def get_or_create(self, key: str) -> object:
        with self._lock:                    # <-- always contend, even on hits
            self.lock_acquisitions += 1
            if key not in self._data:
                self._data[key] = object()
            return self._data[key]


class DoubleCheckedStore:
    """Lock-free fast path; locks only when the key might need creating."""

    def __init__(self) -> None:
        self._data: dict[str, object] = {}
        self._lock = threading.Lock()
        self.lock_acquisitions = 0

    def get_or_create(self, key: str) -> object:
        existing = self._data.get(key)      # 1. lock-free read
        if existing is not None:            #    common case: already exists
            return existing
        with self._lock:                    # 2. rare path: contend for the lock
            self.lock_acquisitions += 1
            if key not in self._data:       # 3. re-check inside the lock
                self._data[key] = object()
            return self._data[key]


def hammer(store, keys: list[str], reps: int) -> None:
    for i in range(reps):
        store.get_or_create(keys[i % len(keys)])


def benchmark(store, label: str, num_threads: int, reps: int, keys: list[str]) -> None:
    threads = [
        threading.Thread(target=hammer, args=(store, keys, reps))
        for _ in range(num_threads)
    ]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start

    total_calls = num_threads * reps
    print(f"{label:20}  time={elapsed * 1000:8.1f} ms   "
          f"lock_acquisitions={store.lock_acquisitions:>7}  of {total_calls} calls")


def main() -> None:
    NUM_THREADS = 32
    REPS = 20_000
    KEYS = [f"k{i}" for i in range(5)]      # only 5 unique keys -> lots of hits

    print(f"{NUM_THREADS} threads x {REPS} reps, {len(KEYS)} unique keys\n")
    benchmark(AlwaysLockStore(),    "AlwaysLock",  NUM_THREADS, REPS, KEYS)
    benchmark(DoubleCheckedStore(), "DoubleChecked", NUM_THREADS, REPS, KEYS)
    print("\nSame correctness; DoubleChecked touches the lock far fewer times,")
    print("so threads stop serializing once the keys are warm -> less contention.")


if __name__ == "__main__":
    main()

##########################
### Response
##########################

# 32 threads x 20000 reps, 5 unique keys

# AlwaysLock            time=   187.8 ms   lock_acquisitions= 640000  of 640000 calls
# DoubleChecked         time=    95.7 ms   lock_acquisitions=      5  of 640000 calls

# Same correctness; DoubleChecked touches the lock far fewer times,
# so threads stop serializing once the keys are warm -> less contention.
