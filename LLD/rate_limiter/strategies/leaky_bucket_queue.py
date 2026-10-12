import asyncio


class LeakyBucket:
    def __init__(self, capacity, leak_rate):
        self.queue = asyncio.Queue(maxsize=capacity)
        self.leak_rate = leak_rate  # requests per second

    async def submit(self, request):
        # Add request to the bucket.
        # Wait if the bucket is full.
        await self.queue.put(request)

    async def worker(self):
        while True:
            request = await self.queue.get()

            try:
                # Process the request
                print(f"Processing {request}")

                # Simulate downstream call
                await process_request(request)

            finally:
                self.queue.task_done()

            # Leak/process at a fixed rate
            await asyncio.sleep(1 / self.leak_rate)


async def process_request(request):
    print(f"  -> sent downstream: {request}")


async def main():
    bucket = LeakyBucket(
        capacity=5,
        leak_rate=1  # 1 request/sec
    )

    # Start worker
    asyncio.create_task(bucket.worker())

    # 5 requests arrive immediately
    for i in range(1, 6):
        await bucket.submit(f"request-{i}")

    print("All requests added to bucket")

    # Wait until all requests are processed
    await bucket.queue.join()


asyncio.run(main())