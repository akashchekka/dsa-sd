"""
=============================================================================
 ThreadPool — entry point / demo
=============================================================================
 Run from inside this folder:  python __main__.py
=============================================================================
"""
from __future__ import annotations

import time

from services.thread_pool import ThreadPool

def square(x: int) -> int:
    time.sleep(0.1)          # simulate slow I/O-bound work
    return x * x

def boom() -> None:
    raise ValueError("task failed")

def main() -> None:
    with ThreadPool(num_workers=3) as pool:
        # 1. fan out work, collect results via futures
        futures = [pool.submit(square, i) for i in range(6)]
        print("squares:", [f.result() for f in futures])

        # 2. exceptions propagate through Future.result()
        bad = pool.submit(boom)
        try:
            bad.result()
        except ValueError as exc:
            print("caught:", exc)

    # 3. leaving the 'with' block shuts down and drains the pool


if __name__ == "__main__":
    main()
