import asyncio
from collections import defaultdict


class LeakyBucketSystem:
    def __init__(self, capacity=5, leak_rate=10):
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests/sec

        # One lightweight queue per active user
        self.queues = defaultdict(
            lambda: asyncio.Queue(maxsize=capacity)
        )

        # Users that currently have work
        self.ready_users = asyncio.Queue()

        # Prevent same user from being added multiple times
        self.scheduled = set()
        self.lock = asyncio.Lock()

    async def submit(self, user_id, request):
        queue = self.queues[user_id]

        # Backpressure: waits if user's bucket is full
        await queue.put(request)

        # Schedule this user if not already scheduled
        async with self.lock:
            if user_id not in self.scheduled:
                self.scheduled.add(user_id)
                await self.ready_users.put(user_id)

    async def worker(self):
        while True:
            # Get a user that has pending work
            user_id = await self.ready_users.get()

            try:
                queue = self.queues[user_id]

                # Leak ONE request
                request = await queue.get()

                try:
                    await process_downstream(request)
                finally:
                    queue.task_done()

                # This user still has work
                if not queue.empty():
                    await asyncio.sleep(1 / self.leak_rate)

                    await self.ready_users.put(user_id)

                else:
                    # No more work for this user
                    async with self.lock:
                        self.scheduled.discard(user_id)

            finally:
                self.ready_users.task_done()


async def process_downstream(request):
    print(f"Sending downstream: {request}")
    await asyncio.sleep(0.1)


async def main():
    system = LeakyBucketSystem(
        capacity=5,
        leak_rate=10
    )

    # Only 10 shared workers for ALL users
    for _ in range(10):
        asyncio.create_task(system.worker())

    # Imagine requests coming from many users
    await system.submit("user-A", "A1")
    await system.submit("user-A", "A2")
    await system.submit("user-A", "A3")

    await system.submit("user-B", "B1")
    await system.submit("user-B", "B2")

    await asyncio.sleep(2)


asyncio.run(main())