---
title: Garbage Collection in .NET for Interviews
description: Interview notes on the .NET garbage collector for C# engineers, covering reachability, generations, the Large and Pinned Object Heaps, Workstation and Server GC, DATAS, finalizers and IDisposable, serialization churn, GC pressure versus memory leaks, diagnosis, tuning, and how GC pauses affect distributed systems
---

## Why GC matters in system design

Interviewers rarely ask "explain mark-sweep" on its own. GC shows up as a cause
of real production problems:

* p99 latency spikes
* Timeouts and false failure detection, because a paused node looks dead
* Lost leases and split brain
* `OutOfMemoryException` and containers being killed for using too much memory
* Lower capacity, because CPU spent in GC is CPU not serving requests

> [!IMPORTANT]
> "GC turns memory management from a correctness problem into a performance
> problem. In C# I don't free memory myself, but I pay for it in CPU time and
> pauses."

## 1. The core idea: reachability

The .NET GC starts from **GC roots** and follows references. Anything it can
reach is alive. Everything else is garbage.

GC roots in .NET are:

* Local variables and parameters on every thread's stack (and CPU registers)
* Static fields
* GC handles, including pinned handles created with `GCHandle.Alloc`
* Objects waiting for their finalizer to run (the f-reachable queue)

```text
Roots (stacks, statics, handles)
   │
   ▼
 Order ──► User ──► Address        reachable: alive

 Cart ──► Item                     nothing points to Cart: garbage
   ▲        │
   └────────┘                      a cycle, but still garbage for the .NET GC
```

> [!IMPORTANT]
> GC frees **unreachable** objects, not **unused** objects. A memory leak in C#
> is an object you will never use again that is still reachable, for example
> through a static dictionary or an event handler.

## 2. Basic algorithms

| Algorithm              | How it works                                                              | Good                                                 | Bad                                                                               | Used by                                              |
|------------------------|---------------------------------------------------------------------------|------------------------------------------------------|-----------------------------------------------------------------------------------|------------------------------------------------------|
| **Reference counting** | Each object counts who points to it. Free it when the count is 0          | Memory is freed immediately, no big pauses           | Cycles never reach 0, every assignment updates a count (atomic if multi-threaded) | CPython, Swift (ARC), C++ `shared_ptr`. Not .NET     |
| **Mark-sweep**         | Mark everything reachable, then sweep unmarked memory into a free list    | Handles cycles, never moves objects                  | Memory gets fragmented, sweep cost grows with heap size                           | .NET background Gen2 GC, Go                          |
| **Mark-compact**       | Mark, then slide live objects together                                    | No fragmentation, allocation becomes a pointer bump  | Moving objects means updating every reference to them, slower                     | .NET blocking GCs (all generations can be compacted) |
| **Copying**            | Copy live objects from one space to an empty space, discard the old space | Cost depends only on live objects, compacts for free | Needs spare empty space                                                           | Young generation in Node.js (V8)                     |

> [!TIP]
> The key insight: compacting or copying cost depends on what is **alive**, not
> on what is dead. If 95% of Gen0 objects are already dead, the GC moves only
> the 5% and reclaims the rest in one step. That is why collecting short-lived
> garbage is cheap.

## 3. Generations in .NET

The **generational hypothesis**: most objects die young. Request objects, DTOs,
buffers, LINQ iterators, closures, and temporary strings live for
microseconds. Caches, singletons, and connection pools live for the whole
process.

So .NET splits the managed heap by age and size:

```text
Small Object Heap (SOH)
┌──────────────┬──────────────┬─────────────────────────────────┐
│     Gen0     │     Gen1     │              Gen2               │
│ new objects  │ short buffer │       long-lived objects        │
└──────────────┴──────────────┴─────────────────────────────────┘

Large Object Heap (LOH): objects of 85,000 bytes or more, collected with Gen2
Pinned Object Heap (POH, .NET 5+): objects allocated as pinned
```

### Life of an object

1. A new object is allocated in Gen0. Each thread has its own allocation
   context, so allocation is a pointer bump and costs a few instructions.
   Objects of 85,000 bytes or more skip Gen0 and go straight to the LOH.
2. When the Gen0 budget is used up, a **Gen0 GC** runs. Survivors are
   **promoted** to Gen1. Everything else in Gen0 is reclaimed at once.
3. When Gen1 fills up, a **Gen1 GC** promotes its survivors to Gen2. Gen1 is a
   buffer that catches objects that live a little longer than one request.
4. When Gen2 fills up, a **Gen2 GC** (a full GC) runs. It also collects the LOH.

> [!NOTE]
> .NET promotes an object after it survives **one** GC of its generation. There
> is no age counter. One unlucky Gen0 GC in the middle of a request is enough
> to push its objects to Gen1.

### Types of GC in .NET

| Type                           | What it collects         | How                                                                                | Cost                                                         |
|--------------------------------|--------------------------|------------------------------------------------------------------------------------|--------------------------------------------------------------|
| **Gen0 GC**                    | Gen0 only                | Blocking, compacting                                                               | Cheap: proportional to survivors. Usually under a few ms     |
| **Gen1 GC**                    | Gen0 and Gen1            | Blocking, compacting                                                               | Cheap to medium                                              |
| **Background Gen2 GC**         | Whole heap including LOH | Marks and sweeps **while the app runs**. Gen0 and Gen1 GCs can still run during it | Short pauses, but uses CPU and doesn't compact               |
| **Blocking Gen2 GC (full GC)** | Whole heap               | Stop-the-world, can compact                                                        | Expensive: can pause for hundreds of ms or more on big heaps |

### What triggers a GC

* A generation's allocation budget is used up (by far the most common)
* `GC.Collect()` is called
* The OS reports low memory, or the machine's memory load is high (about 90%
  by default)
* The process gets close to its heap hard limit (common in containers)

### Old-to-young references

A Gen0 GC scans only Gen0. But a Gen2 object can point to a Gen0 object, and
that Gen0 object must not be freed.

The fix is a **write barrier** plus a **card table**. Every time code stores a
reference into an object field, a few extra instructions mark that small chunk
of memory as "dirty". The Gen0 GC scans only the dirty chunks of the older
generations as extra roots instead of all of Gen2.

### The mid-life crisis

The .NET GC team's name for the worst pattern: objects live **just long
enough** to reach Gen2, then die soon after. Only expensive Gen2 GCs can
reclaim them. A high Gen2 GC count compared with Gen0 is the symptom. This is
the main way allocation churn turns into long pauses.

## 4. Stop-the-world, suspension, and background GC

**Stop-the-world** means every managed thread is suspended so the object graph
doesn't change while the GC works on it.

The runtime can only suspend a thread at a **safe point**, where it knows
exactly where every reference is. Threads running native code (for example a
P/Invoke call) don't block suspension because they can't touch managed objects
without coming back first. Long suspension times show up in GC traces as
"suspend time".

| Term           | Meaning                                                     |
|----------------|-------------------------------------------------------------|
| **Blocking**   | The application is paused for the whole GC                  |
| **Parallel**   | Many GC threads work together (Server GC)                   |
| **Background** | Gen2 marking and sweeping run at the same time as the app   |
| **Foreground** | A Gen0 or Gen1 GC that runs while a background GC is active |

### Why concurrent GC is hard: tri-color marking

Concurrent collectors mark objects with three colors:

* White: not seen yet, will be freed if it stays white
* Gray: seen, but its references haven't been scanned yet
* Black: seen and fully scanned

The danger: while marking runs, the application stores a white object into a
black object and removes the last gray path to it. The GC never looks at black
objects again, so a live object stays white and gets freed.

**Write barriers** prevent this. The runtime records which memory the
application wrote to during background marking, and the GC re-scans those
areas in a short final pause. That bookkeeping costs a little CPU, which is the
price of short pauses.

## 5. GC modes and settings

### Workstation vs Server GC

| Mode                            | Heaps and GC threads                                                       | Strength                                               | Cost                                    | Default for                                |
|---------------------------------|----------------------------------------------------------------------------|--------------------------------------------------------|-----------------------------------------|--------------------------------------------|
| **Workstation, concurrent**     | One heap. GC runs on the thread that triggered it. Background Gen2         | Low memory, short pauses                               | Lower throughput on many-core machines  | Desktop, console, and UI apps              |
| **Workstation, non-concurrent** | One heap, every GC is blocking                                             | Least overhead                                         | Longer Gen2 pauses                      | Opt-in                                     |
| **Server**                      | One heap and one dedicated GC thread **per logical core**. Background Gen2 | High throughput, parallel GC work                      | Much more memory, bigger Gen0 budgets   | ASP.NET Core apps                          |
| **Server with DATAS**           | Server GC that starts with one heap and adds heaps as load grows           | Server throughput, memory that follows the actual load | Slightly more GC work under bursty load | Opt-in in .NET 8, on by default in .NET 9+ |

DATAS stands for Dynamic Adaptation To Application Sizes. It fixes a common
container problem: classic Server GC on a 32-core node creates 32 heaps, even
for a small service, and uses far more memory than the app needs.

### Configuring the GC

In the project file:

```xml
<PropertyGroup>
  <ServerGarbageCollection>true</ServerGarbageCollection>
  <ConcurrentGarbageCollection>true</ConcurrentGarbageCollection>
  <!-- 1 turns DATAS on, 0 turns it off -->
  <GarbageCollectionAdaptationMode>1</GarbageCollectionAdaptationMode>
</PropertyGroup>
```

In `runtimeconfig.json`:

```json
{
  "configProperties": {
    "System.GC.Server": true,
    "System.GC.Concurrent": true,
    "System.GC.HeapHardLimitPercent": 75
  }
}
```

As environment variables: `DOTNET_gcServer=1`, `DOTNET_GCHeapHardLimitPercent=0x4B`.

> [!CAUTION]
> GC environment variables take **hexadecimal** numbers.
> `DOTNET_GCHeapHardLimitPercent=75` means 117%, not 75%. Use `0x4B`, or set
> the value in `runtimeconfig.json`, which uses decimal.

### Latency modes

`GCSettings.LatencyMode` lets code tell the GC what matters right now:

| Mode                          | Effect                                                                              |
|-------------------------------|-------------------------------------------------------------------------------------|
| `Batch`                       | No background GC. Best throughput, longest pauses                                   |
| `Interactive`                 | The default when concurrent GC is on                                                |
| `SustainedLowLatency`         | Avoids blocking Gen2 GCs while there is enough memory. For latency-critical periods |
| `LowLatency`                  | Workstation only. Suppresses Gen2 GCs for a very short window                       |
| `GC.TryStartNoGCRegion(size)` | No GC at all until `size` bytes are allocated. For tiny, critical code paths        |

### The trade-off triangle

You can optimize for two of these three:

* **Throughput:** percentage of CPU time spent on application work
* **Latency:** how long the longest pauses are
* **Footprint:** how much memory you need

Server GC buys throughput with memory. Background GC buys shorter pauses with
CPU. Workstation GC buys a small footprint with throughput.

### Choosing a configuration

| Workload                                              | Choice                                                                 |
|-------------------------------------------------------|------------------------------------------------------------------------|
| ASP.NET Core API on a dedicated VM                    | Server GC, concurrent (the defaults)                                   |
| ASP.NET Core in containers, or many services per node | Server GC with DATAS (.NET 8+), or cap heaps with `GCHeapCount`        |
| Very small container (1 CPU, a few hundred MB)        | Workstation GC                                                         |
| Batch processing, only total time matters             | Server GC, non-concurrent, or `Batch` latency mode                     |
| Latency-critical window (trading, game frame)         | `SustainedLowLatency`, or `TryStartNoGCRegion` for very short sections |
| Desktop or UI app                                     | Workstation, concurrent (the default)                                  |

## 6. Large Object Heap and pinning

### Large Object Heap (LOH)

* Every object of **85,000 bytes or more** goes to the LOH, usually large arrays
  and strings. A `byte[85000]` or a `List<T>` backing array with about 10,000
  references qualifies.
* The LOH is collected only during Gen2 GCs. Allocating many large temporary
  objects causes **more Gen2 GCs**.
* The LOH is **not compacted by default**, so it fragments. A request for a big
  block can fail or grow the heap even when total free memory is high.
* You can compact it once with
  `GCSettings.LargeObjectHeapCompactionMode = GCLargeObjectHeapCompactionMode.CompactOnce`.

A classic LOH trap is `MemoryStream`. It doubles its internal buffer as it
grows, so serializing a 1 MB payload creates a chain of LOH arrays that are
immediately garbage. `RecyclableMemoryStream` (from Microsoft) pools small
blocks instead.

### Pinning

A pinned object can't be moved by the GC. Pinning is needed when native code
holds a pointer to managed memory (sockets, file I/O, P/Invoke).

* `fixed` blocks pin for a short scope and are cheap
* `GCHandle.Alloc(obj, GCHandleType.Pinned)` pins until you free the handle.
  Forgetting `Free()` is a leak
* Long-lived pins in Gen0 block compaction and fragment the heap
* Since .NET 5, `GC.AllocateArray<T>(length, pinned: true)` puts the array on
  the **Pinned Object Heap**, so it never blocks compaction of other objects.
  ASP.NET Core's Kestrel uses this for its I/O buffers

## 7. Finalizers, IDisposable, and weak references

### Does Dispose free memory

No. This is a common interview trap.

* `Dispose()` releases **unmanaged resources** right away: file handles,
  sockets, database connections, native memory.
* The **managed memory** of the object is freed later by the GC, like any
  other object.

### How finalizers work and why they are costly

1. An object with a finalizer (`~MyClass()`) is registered in the
   finalization queue when it is created.
2. When it becomes unreachable, the GC can't free it yet. It moves it to the
   **f-reachable queue**, which is a root, so the object and everything it
   references **survive and get promoted**.
3. A single finalizer thread runs the finalizers.
4. Only a later GC can reclaim the memory.

So a finalizable object lives for at least one extra GC and often reaches
Gen2. A slow or blocked finalizer stalls the single finalizer thread and the
finalization queue grows without limit, which is a leak.

### The right pattern

* Implement `IDisposable` and use `using` or `await using`
* In `Dispose()`, call `GC.SuppressFinalize(this)` so the finalizer cost is
  skipped
* Wrap native handles in `SafeHandle` instead of writing finalizers yourself
* Only classes that directly own unmanaged resources need a finalizer

### Weak references

| Type                         | Behavior                                                                          |
|------------------------------|-----------------------------------------------------------------------------------|
| `WeakReference<T>`           | Doesn't keep the object alive. `TryGetTarget` fails after the object is collected |
| `ConditionalWeakTable<K, V>` | Attaches data to an object. The entry disappears when the key object is collected |
| Strong reference (normal)    | Keeps the object alive                                                            |

.NET has no "soft" references (kept until memory is low). For caches, use
`MemoryCache` with a `SizeLimit` and expiration instead of weak references.

## 8. How .NET compares with other runtimes

| Runtime              | GC design                                                                                              | Things to know                                                                                                |
|----------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **.NET**             | Generational (Gen0, Gen1, Gen2), compacting, background Gen2, separate LOH and POH                     | Workstation vs Server GC, DATAS, value types (`struct`) and `Span<T>` give you direct control over allocation |
| **Go**               | Concurrent mark-sweep. Not generational and doesn't move objects                                       | Pauses are usually under 1 ms, but marking uses about 25% of CPU. Tuned with `GOGC` and `GOMEMLIMIT`          |
| **Python (CPython)** | Reference counting frees most objects immediately. A separate cycle collector handles reference cycles | The cycle collector can be tuned or frozen with the `gc` module                                               |
| **Node.js (V8)**     | Young generation uses copying, old generation uses mark-compact, mostly concurrent                     | `--max-old-space-size` caps the old generation                                                                |
| **Rust, C, C++**     | No GC. Rust frees memory when the owner goes out of scope (checked at compile time). C++ uses RAII     | Predictable latency, but memory bugs (C, C++) or a stricter compiler (Rust) are the cost                      |

> [!TIP]
> A .NET advantage worth saying in interviews: C# has **value types**. A
> `struct`, a `Span<T>`, or a `stackalloc` buffer never touches the GC heap, so
> you can remove allocations from hot paths without leaving the language.

### Real-world stories

These are useful to mention because they show GC as a design concern, not
trivia.

* **Stack Overflow (.NET):** the team wrote about long Gen2 pauses caused by
  millions of long-lived objects in their in-memory caches. Every Gen2 GC had
  to walk all of them. They cut pauses by storing data as arrays of structs,
  which turns millions of objects into a few.
* **Roslyn (the C# compiler):** the team's performance guidelines avoid LINQ,
  closures, and boxing in hot paths, because the compiler runs inside the IDE
  on every keystroke and GC pauses showed up as typing lag.
* **ASP.NET Core and Kestrel:** built around `System.IO.Pipelines`, pooled
  buffers, and `Span<T>`, so a typical request allocates very little. That is a
  big part of its benchmark results.
* **Discord (Go to Rust):** a Go service with a large in-memory cache had
  latency spikes every 2 minutes, because each forced GC scanned the whole
  cache. They rewrote it in Rust. The same lesson applies to large on-heap
  caches in .NET.
* **Instagram (Python):** the cycle collector wrote to shared memory pages in
  forked worker processes and broke memory sharing. They disabled it and
  reported about 10% better CPU efficiency.

## 9. How serialization causes GC overhead

Serialization doesn't trigger GC directly. It **creates a huge number of
short-lived objects and buffers**, and the GC has to clean them up.

One cache read in a feed service using an older, string-based approach:

```text
Network bytes → byte[] → string (JSON text, UTF-16) → JObject tree → Post object
                 copy 1    copy 2, twice the size      temp objects   final object
```

.NET strings are UTF-16, so turning UTF-8 JSON bytes into a `string` **doubles
the size** and adds a full copy. A 50 KB JSON payload becomes a 100 KB string,
which lands on the LOH.

| Source of garbage        | C# example                                                                             |
|--------------------------|----------------------------------------------------------------------------------------|
| **Buffer copies**        | Socket buffer → `byte[]` → `string`. The same data copied two or three times           |
| **One object per field** | `Post` → `User`, `List<Comment>`, each `string`, each nested class                     |
| **Boxing**               | `int` stored as `object`, in non-generic collections, or through an interface          |
| **Intermediate trees**   | `JObject` and `JToken` (Newtonsoft.Json), `JsonNode`                                   |
| **Growing buffers**      | `MemoryStream` and `StringBuilder` double their buffers and drop the old ones          |
| **Per-call setup**       | `new JsonSerializerOptions()` on every call rebuilds the type metadata cache each time |

Almost all of it, except the final object, is garbage within microseconds.

### Why it hurts

1. **A high allocation rate means frequent GCs.** A feed request loads 50
   posts at about 4 KB of garbage each, so 200 KB per request. At 2,000
   requests per second per server, that is about 400 MB/s of garbage. Gen0
   fills many times a second and GC takes CPU from real work.
2. **Under load, short-lived objects stop being short-lived.** Requests wait on
   slow downstream calls (`await` keeps their objects alive), so their
   deserialized objects are still reachable when a Gen0 GC runs. They get
   promoted to Gen1, then Gen2. That is the mid-life crisis, and it leads to
   more Gen2 GCs and p99 spikes.
3. **Large buffers go to the LOH.** Any payload, string, or buffer of 85,000
   bytes or more is allocated on the LOH, which is collected only in Gen2 and
   fragments.
4. **It feeds on itself.** Pauses slow requests down, so objects live longer,
   more get promoted, and pauses get worse.

### Fixes

| Fix                                                 | How it helps                                                                                     |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Fetch and send fewer fields**                     | Fewer bytes means fewer objects. The cheapest fix                                                |
| **Deserialize from UTF-8 bytes, not strings**       | `JsonSerializer.Deserialize<T>(ReadOnlySpan<byte>)` or from a `Stream` skips the UTF-16 string   |
| **Reuse one `JsonSerializerOptions`**               | Store it in a `static readonly` field so type metadata is built once                             |
| **System.Text.Json source generation**              | A `JsonSerializerContext` creates serialization code at compile time instead of using reflection |
| **`Utf8JsonReader` and `Utf8JsonWriter`**           | Read and write JSON field by field with almost no allocations                                    |
| **Binary formats**                                  | Protobuf (`Google.Protobuf`, `protobuf-net`) or MessagePack: smaller, no text parsing            |
| **`ArrayPool<byte>.Shared`**                        | Rent and return buffers instead of allocating new ones                                           |
| **`RecyclableMemoryStream`**                        | Avoids the `MemoryStream` doubling chain on the LOH                                              |
| **`IBufferWriter<byte>` and `System.IO.Pipelines`** | Serialize straight into the response or socket buffer                                            |
| **Pass bytes through**                              | A service that only forwards data shouldn't deserialize it                                       |
| **Avoid boxing**                                    | Generic collections, `struct`s, and avoiding `object` parameters in hot paths                    |
| **Cache the serialized response**                   | ASP.NET Core output caching or a byte cache: serialize once, not per request                     |
| **Tune the GC**                                     | Server GC, bigger Gen0 budget. This treats the symptom, not the cause                            |

## 10. GC pressure vs memory leak

These are two different problems, and interviewers often check whether you can
tell them apart.

|                        | **GC pressure (churn)**                                 | **Memory leak**                                                             |
|------------------------|---------------------------------------------------------|-----------------------------------------------------------------------------|
| What happens           | Lots of objects are created and **die quickly**         | Objects stay **reachable but are never used again**, so they can't be freed |
| Memory over time       | Sawtooth that returns to the **same baseline** after GC | Sawtooth with a **rising baseline**, and each Gen2 GC frees less            |
| Symptom                | High % time in GC, many Gen0 GCs, p99 latency spikes    | Memory grows for hours or days, Gen2 GCs get longer, then out of memory     |
| Does a restart fix it? | No, it starts right away under load                     | Yes, temporarily. A classic sign of a leak                                  |
| Cause                  | **How much** you allocate                               | **Who still holds a reference**                                             |

### Leaks that come from serialization

| Leak                                        | How it happens                                                                                                                                                      |
|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Unbounded cache of deserialized objects** | A `static ConcurrentDictionary<id, Post>` or a `MemoryCache` with no `SizeLimit` or expiration. The most common one                                                 |
| **`XmlSerializer` created per call**        | Constructors other than `new XmlSerializer(Type)` generate a new dynamic assembly **every time**, and it is never unloaded. Create the serializer once and reuse it |
| **Thread-static buffers**                   | A `[ThreadStatic]` cached `StringBuilder` or `byte[]` grows to 50 MB for one huge payload and never shrinks. Thread pool threads live for the whole process         |
| **Small slice holding a big array**         | A `Memory<byte>` or `ArraySegment<byte>` of 10 bytes, stored in a long-lived object, keeps the whole 5 MB array alive                                               |
| **Native buffers never freed**              | `Marshal.AllocHGlobal` or `NativeMemory.Alloc` without a matching free. Invisible in managed heap snapshots                                                         |
| **Interning keys**                          | `string.Intern` on field names or values from user input. Interned strings are never freed                                                                          |

> [!NOTE]
> Forgetting to return an array to `ArrayPool` is **not** a leak: the GC
> collects it like any other array, and you only lose the pooling benefit. The
> real bug with pools is the opposite one: returning a buffer and then still
> using it, which corrupts another request's data.

### Other common .NET leaks

* **Event handlers:** a short-lived object subscribes to an event on a
  long-lived publisher (`+=`) and never unsubscribes (`-=`). The publisher's
  delegate list keeps the subscriber alive forever. This is the most famous
  .NET leak
* Static collections that only ever grow
* `System.Threading.Timer` objects that are never disposed keep their callback
  and its captured state alive
* Lambdas that capture a large object and are stored in a long-lived place
* Disposable transient services resolved from the root `IServiceProvider` in
  ASP.NET Core: the container tracks them until the app shuts down
* `GCHandle.Alloc` without `Free()`
* A finalizer that blocks, so the single finalizer thread stops and the
  finalization queue grows
* Dynamic assemblies or `AssemblyLoadContext`s that are never unloaded
* Dictionary keys whose `GetHashCode` changes after insert, so lookups miss and
  duplicates pile up

> [!NOTE]
> Creating a new `HttpClient` per request is a **resource** leak, not a memory
> leak: it exhausts sockets. Use `IHttpClientFactory` or one shared
> `HttpClient`.

### When churn looks like a leak

Under heavy load, objects get promoted and Gen2 size **climbs for a while**,
which looks like a leak. The test:

> [!TIP]
> Look at heap size **right after each Gen2 GC**, over hours. Flat means
> churn. Rising means a leak. `GC.GetGCMemoryInfo(GCKind.FullBlocking)` or the
> heap size counter after Gen2 GCs gives you this number.

## 11. Out-of-memory failures in .NET

| Failure                                       | Meaning                                                                                               |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------|
| `OutOfMemoryException` with a full heap       | The heap is full of live objects. Either a leak or the heap limit is too small                        |
| `OutOfMemoryException` with free memory left  | Fragmentation: no contiguous block big enough, usually on the LOH or around pinned objects            |
| `OutOfMemoryException` at the heap hard limit | The GC heap reached `GCHeapHardLimit`. In containers this defaults to 75% of the memory limit         |
| Container `OOMKilled`, no .NET exception      | The **whole process** went over the container limit: native memory, thread stacks, or Server GC heaps |
| Process memory grows, managed heap stays flat | A native memory leak: undisposed native resources, `Marshal.AllocHGlobal`, or native libraries        |

> [!WARNING]
> In a container with a memory limit, .NET caps the GC heap at 75% of that
> limit by default. The remaining 25% is for native memory, thread stacks
> (about 1 MB each on Linux), and JIT-compiled code. Classic Server GC on a
> many-core node can still use far more memory than expected, so enable DATAS
> or set `GCHeapCount`.

## 12. Diagnosing GC problems

### Metrics to watch

* % time in GC: rule of thumb, more than 5% to 10% is worth investigating
* Allocation rate (MB/s): high means churn
* Gen0, Gen1, and Gen2 GC counts: Gen2 rising quickly compared with Gen0 means
  objects are being promoted (mid-life crisis)
* Heap size after Gen2 GCs: rising means a leak
* LOH size and fragmentation
* GC pause durations: p99 and max, not just average. `GC.GetTotalPauseDuration()`
  (.NET 7+) gives the total

### Steps

1. **Watch live counters:** `dotnet-counters monitor -p <pid> --counters System.Runtime`.
2. **Look at the trend of heap size after Gen2 GCs** to separate churn from a
   leak.
3. **For churn,** collect an allocation trace and find which code allocates
   the most. It's usually serialization, string building, LINQ, closures,
   logging, or boxing.
4. **For a leak,** take two heap snapshots a few minutes apart and compare
   them. Find the types that keep growing, then ask **what is holding them**
   (`gcroot` in `dotnet-dump`, or "paths to root" in a profiler). It's usually a
   static dictionary, a cache, an event handler, or a timer.
5. **If process memory is much bigger than the GC heap,** suspect native
   memory: undisposed native resources, pinned or native buffers, or thread
   stacks.

### Tools

| Tool                                        | Use it for                                                                          |
|---------------------------------------------|-------------------------------------------------------------------------------------|
| `dotnet-counters`                           | Live GC metrics: heap size, % time in GC, allocation rate, GC counts per generation |
| `dotnet-gcdump`                             | Lightweight heap snapshots in production. Compare two to find growing types         |
| `dotnet-dump` (`dumpheap -stat`, `gcroot`)  | Full memory dump. `gcroot` shows the chain of references keeping an object alive    |
| `dotnet-trace` (`--profile gc-verbose`)     | GC events and allocation sampling                                                   |
| PerfView                                    | GCStats report: every GC, its pause, and its reason. Allocation stacks              |
| Visual Studio profiler, JetBrains dotMemory | Snapshot comparison and retention paths with a UI                                   |
| BenchmarkDotNet `[MemoryDiagnoser]`         | Bytes allocated per call and GC counts in microbenchmarks                           |
| `GC.GetAllocatedBytesForCurrentThread()`    | Assert allocation budgets in tests                                                  |
| OpenTelemetry runtime metrics               | GC metrics (collections, pause time, heap size) in dashboards and alerts            |

## 13. Reducing GC pressure: fix the code first

| Technique                                            | Why                                                                                                    |
|------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Allocate less per request**                        | Fewer fields, smaller payloads, no intermediate copies                                                 |
| **Pre-size collections**                             | `new List<T>(capacity)`: a growing `List<T>` or `Dictionary` copies itself on every resize             |
| **Use `struct` for small, short-lived data**         | Value types live on the stack or inline in arrays, not as separate heap objects                        |
| **`Span<T>`, `ReadOnlySpan<T>`, `stackalloc`**       | Slice and parse strings and buffers without allocating substrings or copies                            |
| **`ValueTask<T>` on hot paths**                      | Avoids a `Task` allocation when the result is often available synchronously                            |
| **Avoid LINQ and closures in hot paths**             | Each LINQ call allocates iterators and delegates. Captured variables allocate a closure object         |
| **`static` lambdas**                                 | The compiler blocks accidental captures, so no closure is allocated                                    |
| **`ArrayPool<T>` and `ObjectPool<StringBuilder>`**   | Reuse buffers and builders instead of allocating new ones                                              |
| **`string.Create` and interpolated string handlers** | Build strings without temporary pieces                                                                 |
| **Bound every cache**                                | `MemoryCache` with `SizeLimit` and expiration, never a plain static dictionary                         |
| **Store cached values as bytes or structs**          | One `byte[]` or an array of structs per entry instead of a tree of objects. Much less for Gen2 to walk |
| **Move big caches out of the process**               | Redis or another external cache. The GC never scans it                                                 |
| **Avoid finalizers**                                 | Use `IDisposable`, `SafeHandle`, and `GC.SuppressFinalize`                                             |

> [!CAUTION]
> Pooling small objects usually makes things worse. Pooled objects end up in
> Gen2, every reference stored into them goes through the write barrier, and
> you bring back manual memory bugs like using an object after returning it.
> Pool only expensive things: large buffers, `StringBuilder`s, and connections.

## 14. Tuning: second, not first

* Pick the GC mode first: Server GC for services, DATAS in containers,
  Workstation for small containers and desktop apps
* In containers, set `System.GC.HeapHardLimitPercent` to leave room for native
  memory, or rely on the 75% default
* Cap Server GC heaps with `GCHeapCount` when many services share one node
* A larger Gen0 budget (`GCgen0size`) means fewer Gen0 GCs and fewer objects
  promoted by bad timing
* `GCConserveMemory` (0 to 9, .NET 6+) makes the GC compact more aggressively
  to reduce fragmentation, at some CPU cost
* Compact the LOH once after a known large cleanup with
  `GCLargeObjectHeapCompactionMode.CompactOnce`
* Use `SustainedLowLatency` around latency-critical periods
* Don't call `GC.Collect()`. It usually triggers an expensive blocking Gen2 GC
  and disrupts the GC's own budgets

### Bigger heap: good or bad?

* A bigger heap means **fewer** GCs, but a blocking Gen2 GC has more live data
  to mark and compact, so the worst pauses can be **longer**.
* Background GC keeps most Gen2 work concurrent, but fragmentation eventually
  forces a blocking compacting GC.
* Many services prefer **more instances with smaller heaps**: shorter pauses,
  and one paused instance affects a smaller share of traffic.

## 15. GC in distributed systems

### Pauses look like failures

A 5-second pause means no heartbeats for 5 seconds. Other nodes declare the
paused node dead, start a failover, and rebalance its data. Then the node wakes
up, and the cluster flaps.

Mitigations:

* Failure timeouts longer than the worst expected GC pause
* Adaptive failure detectors (phi accrual, used by Akka.NET)
* Keep Gen2 small on coordination-critical nodes and use background GC

### Pauses break leases and locks

```text
1. Service A gets a lock lease valid for 10 s
2. Service A pauses for a blocking Gen2 GC for 15 s
3. Lease expires. Service B gets the lock and writes to storage
4. Service A wakes up, still believes it holds the lock, and writes too
   → two writers, corrupted data
```

The fix is a **fencing token**. The lock service hands out an increasing number
with each lease, and storage rejects writes with a token older than the newest
one it has seen. A process can't detect its own pause reliably, so the safety
check has to live in the storage system.

### Tail latency in fan-out

If each backend is in a GC pause 1% of the time, a request that calls 100
backends hits at least one paused backend about **63%** of the time
(`1 - 0.99^100`).

Mitigations:

* Hedged requests: send a second copy to another replica after a short delay
* Smaller heaps and more instances
* Reduce allocation in the hot path
* Keep large caches out of the GC heap

### Other effects

* **Request pile-up:** requests queue during a pause and arrive all at once
  when it ends. Use backpressure and bounded queues.
* **Large in-process caches:** millions of cached objects make every Gen2 GC
  longer. Prefer external caches, or store entries as bytes or structs.

## 16. Follow-up questions and answers

### Can a C# program have a memory leak

Yes. The GC frees unreachable objects only. If a static dictionary, cache,
event handler, or timer still holds a reference, the object is never freed even
if the code never uses it again.

### How does the .NET GC handle reference cycles

Automatically. The .NET GC traces from roots, so a cycle that no root can
reach is garbage. Pure reference counting can't free cycles, which is why
CPython adds a separate cycle collector and Swift needs `weak` references.

### Why does the GC need to stop the world at all

To get a consistent view of references while moving objects. Background GC
keeps Gen2 marking concurrent, but Gen0 and Gen1 GCs and compaction still need
short pauses.

### Why is a Gen0 GC cheap and a Gen2 GC expensive

A Gen0 GC handles a small area where most objects are dead, so it only moves
the few survivors. A Gen2 GC has to mark the whole heap, most of which is
alive.

### What is the Large Object Heap and why does it matter

Objects of 85,000 bytes or more go there. It is collected only with Gen2 and
not compacted by default, so large temporary buffers cause extra Gen2 GCs and
fragmentation. Pool large buffers instead.

### Does calling Dispose release memory

No. It releases unmanaged resources such as handles, sockets, and connections
right away. The object's managed memory is freed later by the GC.

### Why are finalizers expensive

A finalizable object survives at least one extra GC (it is kept alive in the
f-reachable queue until its finalizer runs), so it often gets promoted to
Gen2. All finalizers run on one thread, so a slow one blocks the rest. Use
`IDisposable`, `SafeHandle`, and `GC.SuppressFinalize`.

### Workstation or Server GC

Server GC uses one heap and GC thread per core for throughput, and is the
default for ASP.NET Core. Workstation GC uses one heap and less memory. In
containers, use Server GC with DATAS, or Workstation GC for very small limits.

### Is calling GC.Collect() a good idea

Almost never. It usually triggers a blocking Gen2 GC and upsets the GC's own
tuning. Let the GC decide.

### How do struct and class differ for the GC

A `class` instance is a separate heap object the GC must track. A `struct` is
stored inline: on the stack, inside another object, or inside an array. An
array of 1 million structs is one object for the GC. An array of 1 million
class instances is 1 million and one objects. Watch out for boxing, which turns
a struct back into a heap object.

### Why can't `Span<T>` be stored on the heap

`Span<T>` is a `ref struct`, so it can only live on the stack. That lets it
safely point into stack memory, native memory, or the middle of an array, and
slice data with no allocation. Use `Memory<T>` when you need to store it in a
field or across `await`.

### Does async/await allocate

Sometimes. If an `async` method completes synchronously, there may be no
allocation at all. If it actually waits, the state machine and the `Task` are
allocated on the heap. `ValueTask<T>` helps on hot paths that usually complete
synchronously.

### What is pinning and why is it bad

Pinning stops the GC from moving an object, so native code can hold a pointer
to it. Long-lived pins in Gen0 block compaction and fragment the heap. Use
short `fixed` blocks, or allocate long-lived buffers on the Pinned Object Heap.

### Should we use a language without GC

Only when predictable latency is a hard requirement and the team can handle it
(Discord's move to Rust is the usual example). In C#, structs, `Span<T>`,
pooling, and the right GC mode are usually enough and much cheaper.

## 17. Answers to say out loud

### Serialization and GC

> "Serialization creates a lot of short-lived objects: buffer copies, UTF-16
> strings twice the size of the payload, one object per field, boxed values,
> and intermediate JSON trees. At high request rates that's hundreds of MB per
> second of garbage, so Gen0 is collected constantly. The bigger problem shows
> up under load. Requests take longer, so their objects survive Gen0 and get
> promoted to Gen2, which means more Gen2 GCs and p99 spikes. Large payloads
> also land on the Large Object Heap. I'd fix it at the source: fetch fewer
> fields, deserialize straight from UTF-8 bytes with System.Text.Json source
> generation, reuse one options instance, pool buffers with `ArrayPool`, skip
> deserializing when a service only forwards data, and cache the serialized
> response. Tuning the GC comes last."

### GC pressure vs memory leak

> "Churn is lots of short-lived garbage. It costs GC CPU and causes latency
> spikes, but the memory is freed. A leak is when objects stay reachable and
> never get freed, so heap size after each Gen2 GC keeps rising until we run
> out of memory. To tell them apart, I look at heap size after Gen2 GCs over
> time. Flat means churn, rising means a leak. For a leak I'd take two
> `dotnet-gcdump` snapshots, find the growing types, and use `gcroot` to see
> what holds them. In .NET it's usually an event handler, a static dictionary,
> an unbounded cache, or a timer."

### GC in a distributed system

> "GC pauses are a distributed systems problem, not only a performance problem.
> A long blocking Gen2 GC looks like a dead node, so I set failure timeouts
> above the worst pause and keep Gen2 small on critical nodes. Pauses can also
> make a process act on an expired lease, so I'd protect storage with fencing
> tokens. In fan-out calls, pauses on a few backends dominate p99, so I'd use
> hedged requests, keep heaps small, and keep allocation low in the hot path."

## Cheat sheet

* The GC frees unreachable objects, not unused ones
* Gen0 for new objects, Gen1 as a buffer, Gen2 for long-lived ones. Survive
  one GC and you are promoted
* Objects of 85,000 bytes or more go to the LOH, which is collected only with
  Gen2 and isn't compacted by default
* Long pauses come from the mid-life crisis: objects promoted to Gen2 that die
  soon after
* Server GC for services, DATAS in containers, Workstation for small apps
* `Dispose` releases unmanaged resources. It doesn't free managed memory
* Finalizers keep objects alive for at least one extra GC. Use `SafeHandle` and
  `GC.SuppressFinalize`
* Churn: high allocation rate, flat heap after Gen2. Leak: heap after Gen2
  keeps rising
* The most common .NET leak is an event handler that is never unsubscribed
* Fix allocation first (`struct`, `Span<T>`, `ArrayPool`, no LINQ in hot
  paths), tune the GC second
* In containers the GC heap defaults to 75% of the memory limit. GC environment
  variables are hexadecimal
* In distributed systems: timeouts above the worst pause, fencing tokens,
  hedged requests

--- 

### .NET GC / Dispose / Finalizer — Quick Revision

#### 1. Managed vs Unmanaged

* **Managed memory** → C#/.NET objects, arrays, strings, etc. → **GC manages their memory**.
* **Unmanaged resources** → OS/native resources such as file handles, sockets, native memory → **GC does not directly manage/release them**.
* A managed object can **own/use** an unmanaged resource.

```text
C# Object
├── Managed fields      → GC
└── Unmanaged resource → Dispose / Finalizer
```

---

#### 2. What does GC do?

* GC primarily **reclaims managed memory** when an object becomes unreachable.
* GC does **not mean "release everything the object owns."**
* An object's memory and the external resources it owns have **different lifetimes**.

---

#### 3. `Dispose()`

* `Dispose()` provides **deterministic cleanup**.
* You explicitly tell an object:

> "I'm done with you; release the resources you're holding now."

Example:

```csharp
using var file = new FileStream(...);
```

When the scope ends → `Dispose()` is called → file handle is released immediately.

* `Dispose()` **does NOT free the C# object's memory**.
* GC will reclaim the object's managed memory later when it becomes unreachable.

```text
Dispose()
   ↓
Release resources NOW
   ↓
Object may still exist in memory
   ↓
No references
   ↓
GC eventually reclaims object memory
```

---

#### 4. Why do we need a Finalizer?

A finalizer is a **backup mechanism** if the programmer forgets to call `Dispose()`.

```text
Forgot Dispose()
      ↓
Object becomes unreachable
      ↓
GC sees finalizer
      ↓
Finalizer runs
      ↓
Unmanaged resource released
      ↓
Later GC reclaims object memory
```

Without a finalizer, the unmanaged resource could remain held until some other mechanism releases it.

---

#### 5. Finalizable objects cost more

A finalizable object generally:

* Cannot be reclaimed immediately in the first GC.
* Gets placed on a **finalization queue**.
* Needs the finalizer thread to run its finalizer.
* Can survive a GC and potentially get **promoted to another generation**.
* Requires another GC later to reclaim its memory.

So finalizers add **GC/finalization overhead**.

---

#### 6. `Dispose(true)` vs `Dispose(false)`

Typical pattern:

```csharp
public void Dispose()
{
    Dispose(true);
    GC.SuppressFinalize(this);
}

protected virtual void Dispose(bool disposing)
{
    if (disposing)
    {
        // Release managed resources
    }

    // Release unmanaged resources
}

~MyResource()
{
    Dispose(false);
}
```

**`Dispose(true)`**

* Explicitly called by application.
* Safe to clean up:

  * Managed resources
  * Unmanaged resources

**`Dispose(false)`**

* Called from finalizer.
* Primarily clean up:

  * Unmanaged resources
* Don't depend on other managed objects being safely available.

---

#### 7. `GC.SuppressFinalize(this)`

After explicit `Dispose()`:

```csharp
Dispose(true);
GC.SuppressFinalize(this);
```

Means:

> **"I've already cleaned up. Don't run my backup finalizer."**

It **doesn't prevent GC from collecting the object**.

It simply prevents unnecessary finalization work.

---

#### 8. Why not just rely on the finalizer?

Because cleanup becomes **non-deterministic**.

You don't know exactly when:

```text
GC → finalizer → resource release
```

will happen.

That can cause scarce resources such as:

* File handles
* Sockets
* Native memory
* Other OS handles

to remain occupied longer than necessary.

**`Dispose()` = preferred cleanup**
**Finalizer = safety net**

---

### 9. The most important mental model

```text
                 Object
                    │
          ┌─────────┴─────────┐
          │                   │
    Managed memory       External resource
          │                   │
          ▼                   ▼
         GC              Dispose()
                              │
                         Finalizer
                         (backup)
```

And remember:

> **GC cleans up managed memory. `Dispose()` provides deterministic resource cleanup. A finalizer is a backup for unmanaged resources when `Dispose()` wasn't called.**

**Interview one-liner:**
**"Dispose controls resource lifetime; GC controls managed-memory lifetime; finalization bridges the two when unmanaged resources weren't explicitly released."**

---

This is the subtle part: **when the finalizer runs, the managed resources are not necessarily safe for your finalizer to use/dispose.**

Suppose:

```csharp
class MyResource
{
    FileStream file;        // managed object
    IntPtr nativeHandle;    // unmanaged resource

    ~MyResource()
    {
        Dispose(false);
    }
}
```

You might think:

> "Finalizer is running → clean both `file` and `nativeHandle`."

But consider:

```text
MyResource
   │
   └── FileStream
```

Both are managed objects. When `MyResource` becomes unreachable, **`FileStream` may also be unreachable**.

The GC is responsible for determining the lifetime of **both objects independently**.

So during finalization, you cannot safely assume:

```text
MyResource's managed references
        ↓
are still valid/usable
```

The runtime does not give you the normal guarantee that they are in a state where your finalizer should call their `Dispose()` methods.

### Why is the unmanaged resource different?

The unmanaged resource is something like:

```text
MyResource
    │
    └── OS HANDLE = 12345
```

GC has no idea what `12345` means or how to release it.

So the finalizer is specifically useful for doing:

```text
Finalizer
   ↓
Release OS/native resource
```

### Therefore

```csharp
Dispose(true)
```

means:

```text
"I'm explicitly being disposed.
My managed references are still usable.
Clean up managed + unmanaged resources."
```

Whereas:

```csharp
Dispose(false)
```

means:

```text
"I'm being finalized.
Don't depend on other managed objects.
Clean up my unmanaged resource."
```

### One important nuance

Modern .NET code often uses **`SafeHandle`** for unmanaged handles. `SafeHandle` itself provides a safer finalization mechanism, so you generally **don't write custom finalizers yourself**.

For interview purposes, remember:

> **`true` = explicit Dispose → managed + unmanaged cleanup.**
> **`false` = finalizer → unmanaged cleanup only, because managed-object lifetime/order isn't something the finalizer should depend on.**

> Finalizers should not depend on the state/lifetime of other managed objects.
