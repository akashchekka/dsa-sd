## 1. Sorting Fundamentals

Sorting rearranges elements according to an ordering rule. Most interview questions
are not asking whether you remember an implementation. They test whether you can
choose an algorithm from the input constraints, preserve required properties, and
recognize a problem that becomes easier after sorting.

### Essential vocabulary

| Property | Meaning | Why it matters |
|---|---|---|
| Stable | Equal keys keep their original relative order | Required for multi-field sorts and event ordering |
| In-place | Uses `O(1)` or very small auxiliary storage | Useful under memory constraints |
| Adaptive | Runs faster when input is already partly sorted | Common for real-world and streaming data |
| Online | Can process values as they arrive | Useful when the full input is unavailable |
| Comparison sort | Learns order only by comparing elements | Subject to the `Omega(n log n)` lower bound |
| Non-comparison sort | Uses key structure such as digits or bounded values | Can achieve linear time under specific constraints |
| Internal sort | All data fits in main memory | Standard interview setting |
| External sort | Data is larger than memory | System design and large-data setting |

### Stability example

Suppose records are already sorted by name:

```text
(80, Ana), (80, Ben), (95, Cara)
```

A stable sort by score preserves `Ana` before `Ben`. An unstable sort may reverse
them. Python's `sorted()` and `list.sort()` are stable.

### The comparison sorting lower bound

A comparison sort can be represented as a decision tree. There are `n!` possible
input permutations, so the tree needs at least `n!` leaves. Its height is therefore:

$$
\log_2(n!) = \Omega(n \log n)
$$

No general comparison-based algorithm can guarantee asymptotically better than
`O(n log n)`. Counting, radix, and bucket sort escape this bound by using more
information about the keys.

## 2. Master Comparison Table

Let `n` be the number of elements, `k` the value range or bucket count, and `d` the
number of digits.

| Algorithm | Best | Average | Worst | Extra space | Stable | Adaptive | Main use |
|---|---:|---:|---:|---:|---|---|---|
| Bubble sort | `O(n)` | `O(n^2)` | `O(n^2)` | `O(1)` | Yes | Yes | Teaching, tiny or nearly sorted input |
| Selection sort | `O(n^2)` | `O(n^2)` | `O(n^2)` | `O(1)` | No | No | Minimize writes |
| Insertion sort | `O(n)` | `O(n^2)` | `O(n^2)` | `O(1)` | Yes | Yes | Small or nearly sorted input |
| Shell sort | Depends | Depends | Usually `O(n^2)` | `O(1)` | No | Partial | Medium in-place input |
| Merge sort | `O(n log n)` | `O(n log n)` | `O(n log n)` | `O(n)` | Yes | No | Stability, linked lists, external sorting |
| Quicksort | `O(n log n)` | `O(n log n)` | `O(n^2)` | `O(log n)` average | No | No | Fast general in-memory sorting |
| 3-way quicksort | `O(n)` for equal keys | `O(n log n)` | `O(n^2)` | `O(log n)` average | No | No | Many duplicate values |
| Heapsort | `O(n log n)` | `O(n log n)` | `O(n log n)` | `O(1)` | No | No | In-place worst-case guarantee |
| Counting sort | `O(n + k)` | `O(n + k)` | `O(n + k)` | `O(n + k)` | Yes | No | Small bounded integer range |
| Radix sort | `O(d(n + k))` | `O(d(n + k))` | `O(d(n + k))` | `O(n + k)` | Yes | No | Fixed-width integers or strings |
| Bucket sort | `O(n + k)` | `O(n + k)` | `O(n^2)` | `O(n + k)` | Depends | No | Approximately uniform distribution |
| Cycle sort | `O(n^2)` | `O(n^2)` | `O(n^2)` | `O(1)` | No | No | Minimum number of writes |
| Timsort | `O(n)` | `O(n log n)` | `O(n log n)` | `O(n)` | Yes | Yes | Production sorting, Python and Java objects |
| Introsort | `O(n log n)` | `O(n log n)` | `O(n log n)` | `O(log n)` | No | Partial | Production sorting, C++ `std::sort` |

> [!IMPORTANT]
> Complexity alone does not choose the algorithm. Ask about stability, memory,
> duplicate frequency, key range, existing order, data size, and data structure.

## 3. Interview Decision Guide

Use the strongest known constraint:

| Situation | Preferred technique | Reason |
|---|---|---|
| General Python interview code | `sorted()` or `.sort()` | Reliable, stable, adaptive `O(n log n)` |
| Need a stable general sort | Merge sort or Timsort | Equal-key order is preserved |
| Need `O(1)` extra space and worst-case `O(n log n)` | Heapsort | Deterministic bound with constant auxiliary space |
| Fast average in-memory sort | Randomized quicksort | Good locality and small constants |
| Many duplicate values | 3-way partition quicksort | Groups all equal values in one pass |
| Input is small or nearly sorted | Insertion sort | Adaptive and low overhead |
| Integers lie in a small range | Counting sort | `O(n + k)` without comparisons |
| Fixed-width integers | Radix sort | Linear in number of digits |
| Values are uniformly distributed | Bucket sort | Expected linear time |
| Need only the kth value | Quickselect | Expected `O(n)` without fully sorting |
| Need the smallest or largest `k` values | Heap or quickselect | Avoids unnecessary full sorting |
| Stream of values | Heap or balanced search tree | Maintains order statistics incrementally |
| Linked list | Merge sort | Splitting and merging do not require random access |
| Data does not fit in memory | External merge sort | Sequential I/O and bounded memory |
| Each value is at most `k` positions away | Min-heap of size `k + 1` | `O(n log k)` |

### Five questions to ask before coding

1. What are `n` and the key constraints?
2. Must the result be stable?
3. Can the input be mutated, and what extra space is allowed?
4. Is the input nearly sorted, duplicate-heavy, bounded, or uniformly distributed?
5. Is a full ordering required, or only a kth element, top `k`, or grouped result?

## 4. Elementary Sorting Algorithms

These algorithms are quadratic, but they still appear in interviews as building
blocks and follow-up discussions.

### Bubble sort

Repeatedly swap adjacent inverted pairs. After each pass, the largest remaining
element has moved to its final position.

```python
def bubble_sort(nums: list[int]) -> list[int]:
    for end in range(len(nums) - 1, 0, -1):
        swapped = False
        for index in range(end):
            if nums[index] > nums[index + 1]:
                nums[index], nums[index + 1] = nums[index + 1], nums[index]
                swapped = True
        if not swapped:
            break
    return nums
```

Loop invariant: after each outer pass, `nums[end:]` is sorted and final.

* Best case: `O(n)` with the `swapped` optimization
* Worst case: `O(n^2)`
* Stable and in-place

### Selection sort

Find the minimum in the unsorted suffix and place it at the next position.

```python
def selection_sort(nums: list[int]) -> list[int]:
    for start in range(len(nums)):
        min_index = start
        for index in range(start + 1, len(nums)):
            if nums[index] < nums[min_index]:
                min_index = index
        nums[start], nums[min_index] = nums[min_index], nums[start]
    return nums
```

* Always `O(n^2)` comparisons
* At most `O(n)` swaps, useful when writes are expensive
* In-place but not stable in its usual form

### Insertion sort

Maintain a sorted prefix and insert each new element into its correct position.

```python
def insertion_sort(nums: list[int]) -> list[int]:
    for index in range(1, len(nums)):
        value = nums[index]
        position = index - 1

        while position >= 0 and nums[position] > value:
            nums[position + 1] = nums[position]
            position -= 1

        nums[position + 1] = value
    return nums
```

* Best case: `O(n)`
* Worst case: `O(n^2)`
* Stable, adaptive, online, and in-place
* Often used inside hybrid sorts for small partitions

Insertion sort performs `O(n + I)` work, where `I` is the number of inversions.
This explains why it performs well on nearly sorted data.

### Binary insertion sort

Binary search finds the insertion point in `O(log n)`, but shifting still costs
`O(n)`. The total worst-case complexity remains `O(n^2)`.

```python
from bisect import bisect_right


def binary_insertion_sort(nums: list[int]) -> list[int]:
    for index in range(1, len(nums)):
        value = nums[index]
        insertion_index = bisect_right(nums, value, 0, index)
        nums[insertion_index + 1 : index + 1] = nums[insertion_index:index]
        nums[insertion_index] = value
    return nums
```

Using `bisect_right` places a new equal key after existing equal keys, preserving
stability.

### Shell sort

Shell sort performs insertion sort over progressively smaller gaps. It reduces
long-distance inversions before the final gap-one pass.

```python
def shell_sort(nums: list[int]) -> list[int]:
    gap = len(nums) // 2

    while gap > 0:
        for index in range(gap, len(nums)):
            value = nums[index]
            position = index

            while position >= gap and nums[position - gap] > value:
                nums[position] = nums[position - gap]
                position -= gap

            nums[position] = value
        gap //= 2

    return nums
```

Its exact complexity depends on the gap sequence. Know the idea, but prefer an
algorithm with clearer guarantees unless the interviewer asks for Shell sort.

## 5. Merge Sort

Merge sort divides the array, recursively sorts both halves, and merges them.

```python
def merge_sort(nums: list[int]) -> list[int]:
    if len(nums) <= 1:
        return nums[:]

    middle = len(nums) // 2
    left = merge_sort(nums[:middle])
    right = merge_sort(nums[middle:])
    return merge(left, right)


def merge(left: list[int], right: list[int]) -> list[int]:
    result = []
    left_index = right_index = 0

    while left_index < len(left) and right_index < len(right):
        if left[left_index] <= right[right_index]:
            result.append(left[left_index])
            left_index += 1
        else:
            result.append(right[right_index])
            right_index += 1

    result.extend(left[left_index:])
    result.extend(right[right_index:])
    return result
```

* Time: `O(n log n)` in every case
* Space: `O(n)` for arrays
* Stable because ties are taken from the left half first
* Recursion depth: `O(log n)`

### Bottom-up merge sort

The iterative form avoids recursion and merges runs of size 1, 2, 4, 8, and so on.

```python
def bottom_up_merge_sort(nums: list[int]) -> list[int]:
    result = nums[:]
    auxiliary = [0] * len(result)
    width = 1

    while width < len(result):
        for left in range(0, len(result), 2 * width):
            middle = min(left + width, len(result))
            right = min(left + 2 * width, len(result))
            merge_ranges(result, auxiliary, left, middle, right)
        width *= 2

    return result


def merge_ranges(
    nums: list[int],
    auxiliary: list[int],
    left: int,
    middle: int,
    right: int,
) -> None:
    auxiliary[left:right] = nums[left:right]
    first, second = left, middle

    for write in range(left, right):
        if first >= middle:
            nums[write] = auxiliary[second]
            second += 1
        elif second >= right:
            nums[write] = auxiliary[first]
            first += 1
        elif auxiliary[first] <= auxiliary[second]:
            nums[write] = auxiliary[first]
            first += 1
        else:
            nums[write] = auxiliary[second]
            second += 1
```

### Merge sort for a linked list

Merge sort is the standard linked-list sort because merging changes pointers and
does not need random access.

```python
class ListNode:
    def __init__(self, value: int = 0, next_node: "ListNode | None" = None):
        self.value = value
        self.next = next_node


def sort_linked_list(head: ListNode | None) -> ListNode | None:
    if head is None or head.next is None:
        return head

    slow = head
    fast = head.next
    while fast is not None and fast.next is not None:
        slow = slow.next
        fast = fast.next.next

    right = slow.next
    slow.next = None
    left = sort_linked_list(head)
    right = sort_linked_list(right)
    return merge_lists(left, right)


def merge_lists(
    first: ListNode | None,
    second: ListNode | None,
) -> ListNode | None:
    sentinel = ListNode()
    tail = sentinel

    while first is not None and second is not None:
        if first.value <= second.value:
            tail.next = first
            first = first.next
        else:
            tail.next = second
            second = second.next
        tail = tail.next

    tail.next = first if first is not None else second
    return sentinel.next
```

## 6. Quicksort and Partitioning

Quicksort partitions values around a pivot, then recursively sorts the partitions.
Its cache locality and small constants make it fast in practice.

### Lomuto partition

Lomuto partition is easy to derive but performs many swaps and handles duplicates
poorly.

```python
import random


def quicksort(nums: list[int]) -> list[int]:
    def sort(left: int, right: int) -> None:
        if left >= right:
            return

        pivot_index = random.randint(left, right)
        nums[pivot_index], nums[right] = nums[right], nums[pivot_index]
        boundary = partition(left, right)
        sort(left, boundary - 1)
        sort(boundary + 1, right)

    def partition(left: int, right: int) -> int:
        pivot = nums[right]
        boundary = left

        for index in range(left, right):
            if nums[index] <= pivot:
                nums[boundary], nums[index] = nums[index], nums[boundary]
                boundary += 1

        nums[boundary], nums[right] = nums[right], nums[boundary]
        return boundary

    sort(0, len(nums) - 1)
    return nums
```

Randomization makes consistently unbalanced partitions unlikely, but the formal
worst case remains `O(n^2)`.

### Hoare partition

Hoare partition scans inward from both ends and usually performs fewer swaps. The
returned index separates two ranges; it is not necessarily the pivot's final index.

```python
def hoare_partition(nums: list[int], left: int, right: int) -> int:
    pivot = nums[(left + right) // 2]
    low = left - 1
    high = right + 1

    while True:
        low += 1
        while nums[low] < pivot:
            low += 1

        high -= 1
        while nums[high] > pivot:
            high -= 1

        if low >= high:
            return high

        nums[low], nums[high] = nums[high], nums[low]
```

Recurse on `[left, split]` and `[split + 1, right]` after Hoare partitioning.

### Three-way quicksort

Dutch National Flag partitioning creates regions smaller than, equal to, and larger
than the pivot. It is the preferred quicksort variant for duplicate-heavy input.

```python
def three_way_quicksort(nums: list[int]) -> list[int]:
    def sort(left: int, right: int) -> None:
        if left >= right:
            return

        pivot = nums[(left + right) // 2]
        smaller = current = left
        larger = right

        while current <= larger:
            if nums[current] < pivot:
                nums[smaller], nums[current] = nums[current], nums[smaller]
                smaller += 1
                current += 1
            elif nums[current] > pivot:
                nums[current], nums[larger] = nums[larger], nums[current]
                larger -= 1
            else:
                current += 1

        sort(left, smaller - 1)
        sort(larger + 1, right)

    sort(0, len(nums) - 1)
    return nums
```

### Pivot strategy and recursion safety

* A fixed first or last pivot degrades on already sorted input
* A random pivot gives expected `O(n log n)` behavior for any fixed input
* Median-of-three often improves practical balance
* Recurse into the smaller partition first and loop over the larger partition to
  keep stack space at `O(log n)` even when partitions are uneven

## 7. Heapsort

A max-heap stores the largest value at index 0. Build the heap in `O(n)`, repeatedly
move the maximum to the end, and restore the heap property.

```python
def heapsort(nums: list[int]) -> list[int]:
    size = len(nums)

    for index in range(size // 2 - 1, -1, -1):
        sift_down(nums, index, size)

    for end in range(size - 1, 0, -1):
        nums[0], nums[end] = nums[end], nums[0]
        sift_down(nums, 0, end)

    return nums


def sift_down(nums: list[int], root: int, size: int) -> None:
    while True:
        largest = root
        left = 2 * root + 1
        right = left + 1

        if left < size and nums[left] > nums[largest]:
            largest = left
        if right < size and nums[right] > nums[largest]:
            largest = right
        if largest == root:
            return

        nums[root], nums[largest] = nums[largest], nums[root]
        root = largest
```

* Build heap: `O(n)`, not `O(n log n)`
* Full sort: `O(n log n)` in every case
* Extra space: `O(1)`
* Not stable
* Usually slower than quicksort in practice because of weaker cache locality

The build is linear because most nodes are near the leaves and move only a short
distance.

## 8. Non-Comparison Sorting

### Counting sort

Counting sort records how many times each integer occurs. A stable version uses
prefix sums to calculate final positions.

```python
def counting_sort(nums: list[int]) -> list[int]:
    if not nums:
        return []

    minimum = min(nums)
    maximum = max(nums)
    counts = [0] * (maximum - minimum + 1)

    for value in nums:
        counts[value - minimum] += 1

    for index in range(1, len(counts)):
        counts[index] += counts[index - 1]

    result = [0] * len(nums)
    for value in reversed(nums):
        count_index = value - minimum
        counts[count_index] -= 1
        result[counts[count_index]] = value

    return result
```

Iterating backward during placement preserves the relative order of equal keys.
Use counting sort only when `k = maximum - minimum + 1` is reasonably close to `n`.

### Radix sort

Least-significant-digit radix sort applies a stable counting sort to each digit,
from right to left.

```python
def radix_sort_nonnegative(nums: list[int]) -> list[int]:
    if not nums:
        return []

    result = nums[:]
    exponent = 1
    maximum = max(result)

    while maximum // exponent > 0:
        result = counting_sort_by_digit(result, exponent)
        exponent *= 10

    return result


def counting_sort_by_digit(nums: list[int], exponent: int) -> list[int]:
    counts = [0] * 10
    result = [0] * len(nums)

    for value in nums:
        digit = (value // exponent) % 10
        counts[digit] += 1

    for digit in range(1, 10):
        counts[digit] += counts[digit - 1]

    for value in reversed(nums):
        digit = (value // exponent) % 10
        counts[digit] -= 1
        result[counts[digit]] = value

    return result


def radix_sort(nums: list[int]) -> list[int]:
    negatives = [-value for value in nums if value < 0]
    nonnegatives = [value for value in nums if value >= 0]
    sorted_negatives = radix_sort_nonnegative(negatives)
    sorted_nonnegatives = radix_sort_nonnegative(nonnegatives)
    return [-value for value in reversed(sorted_negatives)] + sorted_nonnegatives
```

The per-digit sort must be stable. Otherwise, ordering established by earlier digits
is destroyed.

### Bucket sort

For values distributed uniformly over `[0, 1)`, distribute values into buckets,
sort each bucket, and concatenate them.

```python
def bucket_sort(values: list[float]) -> list[float]:
    if not values:
        return []
    if any(value < 0 or value >= 1 for value in values):
        raise ValueError("bucket_sort expects values in [0, 1)")

    buckets = [[] for _ in values]
    for value in values:
        bucket_index = min(int(value * len(values)), len(values) - 1)
        buckets[bucket_index].append(value)

    result = []
    for bucket in buckets:
        insertion_sort_bucket(bucket)
        result.extend(bucket)
    return result


def insertion_sort_bucket(values: list[float]) -> None:
    for index in range(1, len(values)):
        value = values[index]
        position = index - 1
        while position >= 0 and values[position] > value:
            values[position + 1] = values[position]
            position -= 1
        values[position + 1] = value
```

Expected time is `O(n + k)` under a uniform distribution. If all values land in one
bucket, the worst case depends on the inner sort and can be `O(n^2)`.

## 9. Specialized and Hybrid Sorts

### Cycle sort

Cycle sort places each value directly into its final position. It minimizes writes,
which matters for flash memory or storage with expensive writes.

```python
def cycle_sort(nums: list[int]) -> list[int]:
    for cycle_start in range(len(nums) - 1):
        value = nums[cycle_start]
        position = cycle_start

        for index in range(cycle_start + 1, len(nums)):
            if nums[index] < value:
                position += 1

        if position == cycle_start:
            continue

        while position < len(nums) and value == nums[position]:
            position += 1
        nums[position], value = value, nums[position]

        while position != cycle_start:
            position = cycle_start
            for index in range(cycle_start + 1, len(nums)):
                if nums[index] < value:
                    position += 1

            while position < len(nums) and value == nums[position]:
                position += 1
            nums[position], value = value, nums[position]

    return nums
```

Cycle sort is not a default choice. Know its write-minimization property.

### Timsort

Timsort combines insertion sort and merge sort:

* Detect naturally ascending or descending runs
* Extend short runs with insertion sort
* Merge runs while maintaining balance invariants
* Use galloping search when one run repeatedly wins

It is stable, adaptive, and has `O(n log n)` worst-case time. Python uses Timsort for
`sorted()` and `list.sort()`.

### Introsort

Introsort starts with quicksort, switches to heapsort when recursion becomes too
deep, and commonly uses insertion sort for tiny partitions. It combines quicksort's
practical speed with heapsort's `O(n log n)` worst-case guarantee. C++ `std::sort`
is typically introsort-based.

### External merge sort

When data exceeds RAM:

1. Read a memory-sized chunk
2. Sort the chunk in memory
3. Write the sorted run to disk
4. Perform a `k`-way merge of all runs using a min-heap

Sequential reads and writes reduce expensive random I/O. The merge heap stores one
front element per run, using `O(k)` memory.

### Parallel sorting

Merge sort parallelizes naturally because its halves are independent. Parallel
quicksort can process partitions concurrently after partitioning. In system design,
distributed sorting usually follows range partitioning, local sorting, and a final
merge or ordered concatenation.

## 10. Python Sorting in Interviews

Python's built-ins should be the default unless the interviewer explicitly asks you
to implement a sorting algorithm.

```python
records = [
    {"name": "Mia", "score": 90},
    {"name": "Ava", "score": 90},
    {"name": "Leo", "score": 75},
]

ordered = sorted(records, key=lambda record: (-record["score"], record["name"]))
records.sort(key=lambda record: record["name"])
```

* `sorted(iterable)` returns a new list
* `list.sort()` mutates the list and returns `None`
* `key` is evaluated once per element
* `reverse=True` reverses the ordering while retaining stability
* Tuple keys provide lexicographic multi-field ordering

### Comparator to key conversion

Prefer key functions. Use `cmp_to_key` only when the ordering depends on comparing
two values directly, as in Largest Number.

```python
from functools import cmp_to_key


def largest_number(nums: list[int]) -> str:
    values = [str(value) for value in nums]

    def compare(first: str, second: str) -> int:
        if first + second > second + first:
            return -1
        if first + second < second + first:
            return 1
        return 0

    result = "".join(sorted(values, key=cmp_to_key(compare)))
    return "0" if result[0] == "0" else result
```

Comparator requirements:

* Antisymmetry: if `a < b`, then `b` must not be less than `a`
* Transitivity: if `a < b` and `b < c`, then `a < c`
* Equality consistency: equivalent values should compare as equal

## 11. Core Sorting Patterns

### Sort then scan

Sorting places related values next to one another. A linear scan can then detect
duplicates, merge intervals, or apply two pointers.

```python
def contains_duplicate(nums: list[int]) -> bool:
    nums.sort()
    return any(nums[index] == nums[index - 1] for index in range(1, len(nums)))
```

Trade `O(n log n)` time for low conceptual complexity and often `O(1)` extra space.

### Merge overlapping intervals

```python
def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    intervals.sort(key=lambda interval: interval[0])
    merged = []

    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    return merged
```

The sort establishes the invariant that no unseen interval starts before the current
one.

### Meeting rooms and event sweeps

Sort starts and ends separately. A meeting starts before the earliest active meeting
ends only when another room is required.

```python
def min_meeting_rooms(intervals: list[list[int]]) -> int:
    if not intervals:
        return 0

    starts = sorted(interval[0] for interval in intervals)
    ends = sorted(interval[1] for interval in intervals)
    end_index = 0
    active = maximum = 0

    for start in starts:
        while end_index < len(ends) and ends[end_index] <= start:
            active -= 1
            end_index += 1
        active += 1
        maximum = max(maximum, active)

    return maximum
```

An equivalent event sweep sorts `(time, delta)` events. Tie ordering matters: process
an ending event before a starting event when touching intervals do not overlap.

### Two pointers after sorting

```python
def three_sum(nums: list[int]) -> list[list[int]]:
    nums.sort()
    triplets = []

    for index in range(len(nums) - 2):
        if index > 0 and nums[index] == nums[index - 1]:
            continue
        if nums[index] > 0:
            break

        left, right = index + 1, len(nums) - 1
        while left < right:
            total = nums[index] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                triplets.append([nums[index], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1

    return triplets
```

Sorting converts a three-variable search from `O(n^3)` to `O(n^2)`.

### Merge two sorted arrays in place

Write from the back so unread values in the first array are not overwritten.

```python
def merge_sorted_arrays(nums1: list[int], m: int, nums2: list[int], n: int) -> None:
    first = m - 1
    second = n - 1
    write = m + n - 1

    while second >= 0:
        if first >= 0 and nums1[first] > nums2[second]:
            nums1[write] = nums1[first]
            first -= 1
        else:
            nums1[write] = nums2[second]
            second -= 1
        write -= 1
```

### K-way merge

Use a min-heap containing the next candidate from each sorted input.

```python
import heapq


def merge_k_sorted_arrays(arrays: list[list[int]]) -> list[int]:
    heap = []
    for array_index, array in enumerate(arrays):
        if array:
            heapq.heappush(heap, (array[0], array_index, 0))

    result = []
    while heap:
        value, array_index, element_index = heapq.heappop(heap)
        result.append(value)
        next_index = element_index + 1
        if next_index < len(arrays[array_index]):
            next_value = arrays[array_index][next_index]
            heapq.heappush(heap, (next_value, array_index, next_index))

    return result
```

For `N` total elements across `k` inputs, time is `O(N log k)` and auxiliary space
is `O(k)`.

### Count inversions during merge sort

An inversion is a pair `(i, j)` where `i < j` and `nums[i] > nums[j]`. When a right
value wins during merging, it forms inversions with every unmerged left value.

```python
def count_inversions(nums: list[int]) -> int:
    auxiliary = [0] * len(nums)

    def sort_and_count(left: int, right: int) -> int:
        if right - left <= 1:
            return 0

        middle = (left + right) // 2
        inversions = sort_and_count(left, middle)
        inversions += sort_and_count(middle, right)

        first, second, write = left, middle, left
        while first < middle and second < right:
            if nums[first] <= nums[second]:
                auxiliary[write] = nums[first]
                first += 1
            else:
                auxiliary[write] = nums[second]
                second += 1
                inversions += middle - first
            write += 1

        while first < middle:
            auxiliary[write] = nums[first]
            first += 1
            write += 1
        while second < right:
            auxiliary[write] = nums[second]
            second += 1
            write += 1

        nums[left:right] = auxiliary[left:right]
        return inversions

    return sort_and_count(0, len(nums))
```

This pattern also solves Reverse Pairs and Count of Smaller Numbers After Self with
modified counting conditions.

## 12. Partial Sorting and Order Statistics

Do not fully sort when the output asks for only a small portion of the order.

### Quickselect

Quickselect partitions only the side containing the target. It runs in expected
`O(n)` time and has `O(n^2)` worst-case time with unlucky pivots.

```python
import random


def kth_largest(nums: list[int], k: int) -> int:
    if not 1 <= k <= len(nums):
        raise ValueError("k is outside the array")

    target = len(nums) - k
    left, right = 0, len(nums) - 1

    while left <= right:
        pivot_index = random.randint(left, right)
        nums[pivot_index], nums[right] = nums[right], nums[pivot_index]
        boundary = left

        for index in range(left, right):
            if nums[index] <= nums[right]:
                nums[boundary], nums[index] = nums[index], nums[boundary]
                boundary += 1

        nums[boundary], nums[right] = nums[right], nums[boundary]

        if boundary == target:
            return nums[boundary]
        if boundary < target:
            left = boundary + 1
        else:
            right = boundary - 1

    raise RuntimeError("unreachable")
```

Median of medians can guarantee worst-case `O(n)`, but its constants and complexity
make it uncommon unless the interviewer explicitly requests a deterministic bound.

### Top k with a heap

Maintain a min-heap of the `k` largest values seen so far.

```python
import heapq


def top_k_largest(nums: list[int], k: int) -> list[int]:
    if k <= 0:
        return []

    heap = []
    for value in nums:
        if len(heap) < k:
            heapq.heappush(heap, value)
        elif value > heap[0]:
            heapq.heapreplace(heap, value)

    return sorted(heap, reverse=True)
```

* Heap: `O(n log k)` time, `O(k)` space, supports streams
* Quickselect: expected `O(n)` time, mutates input, best for batch data
* Full sort: `O(n log n)`, useful when all ranks will be queried

### Sort a k-sorted array

If every value is at most `k` positions away from its final position, the smallest
remaining value must be among the next `k + 1` values.

```python
import heapq


def sort_k_sorted(nums: list[int], k: int) -> list[int]:
    if not nums:
        return []

    heap = nums[: min(k + 1, len(nums))]
    heapq.heapify(heap)
    result = []

    for index in range(k + 1, len(nums)):
        result.append(heapq.heapreplace(heap, nums[index]))

    while heap:
        result.append(heapq.heappop(heap))

    return result
```

Time is `O(n log k)` and space is `O(k)`.

## 13. Index Placement Patterns

These problems resemble sorting but exploit a narrow value range to run in linear
time with constant extra space.

### Cyclic sort for values 1 through n

```python
def cyclic_sort(nums: list[int]) -> list[int]:
    index = 0
    while index < len(nums):
        correct_index = nums[index] - 1
        if nums[index] != nums[correct_index]:
            nums[index], nums[correct_index] = nums[correct_index], nums[index]
        else:
            index += 1
    return nums
```

Each swap places at least one value in its final position, so there are at most
`O(n)` swaps. Common variations find a missing number, duplicate number, corrupt
pair, or first missing positive.

### First missing positive

```python
def first_missing_positive(nums: list[int]) -> int:
    size = len(nums)
    index = 0

    while index < size:
        value = nums[index]
        correct_index = value - 1
        if 1 <= value <= size and nums[correct_index] != value:
            nums[index], nums[correct_index] = nums[correct_index], nums[index]
        else:
            index += 1

    for index, value in enumerate(nums):
        if value != index + 1:
            return index + 1
    return size + 1
```

### Dutch National Flag

Sort three distinct values in one pass using low, current, and high boundaries.

```python
def sort_colors(nums: list[int]) -> None:
    low = current = 0
    high = len(nums) - 1

    while current <= high:
        if nums[current] == 0:
            nums[low], nums[current] = nums[current], nums[low]
            low += 1
            current += 1
        elif nums[current] == 2:
            nums[current], nums[high] = nums[high], nums[current]
            high -= 1
        else:
            current += 1
```

Do not advance `current` after swapping with `high`; the incoming value has not been
classified.

### Wiggle sort

For the non-strict relation `nums[0] <= nums[1] >= nums[2] <= nums[3]`, a local
one-pass repair is sufficient.

```python
def wiggle_sort(nums: list[int]) -> None:
    for index in range(1, len(nums)):
        should_swap = (
            index % 2 == 1 and nums[index] < nums[index - 1]
        ) or (
            index % 2 == 0 and nums[index] > nums[index - 1]
        )
        if should_swap:
            nums[index], nums[index - 1] = nums[index - 1], nums[index]
```

The strict Wiggle Sort II variant requires duplicate-aware median partitioning or a
careful sorted interleaving.

## 14. Common Interview Problems

### Easy

| Problem | Main technique |
|---|---|
| Merge Sorted Array, LC 88 | Backward two-pointer merge |
| Squares of a Sorted Array, LC 977 | Two pointers from both ends |
| Sort Array by Parity, LC 905 | Two-way partition |
| Height Checker, LC 1051 | Counting sort or compare with sorted copy |
| Relative Sort Array, LC 1122 | Counting or custom key |
| Missing Number, LC 268 | Cyclic placement, XOR, or arithmetic |

### Medium

| Problem | Main technique |
|---|---|
| Sort Colors, LC 75 | Dutch National Flag |
| Sort an Array, LC 912 | Merge, heap, or randomized quicksort |
| Kth Largest Element, LC 215 | Quickselect or heap |
| Top K Frequent Elements, LC 347 | Bucket sort or heap |
| Merge Intervals, LC 56 | Sort then scan |
| Insert Interval, LC 57 | Ordered interval merge |
| Meeting Rooms II, LC 253 | Sweep line or min-heap |
| Largest Number, LC 179 | Custom comparator |
| H-Index, LC 274 | Counting sort or descending sort |
| Sort List, LC 148 | Linked-list merge sort |
| Queue Reconstruction by Height, LC 406 | Sort by one key, insert by another |
| Car Fleet, LC 853 | Sort positions, scan arrival times |
| Find All Duplicates, LC 442 | Index placement or sign marking |
| Maximum Gap, LC 164 | Bucket or radix sort |
| Wiggle Sort II, LC 324 | Median plus virtual-index partition |

### Hard

| Problem | Main technique |
|---|---|
| First Missing Positive, LC 41 | Cyclic index placement |
| Count of Smaller Numbers After Self, LC 315 | Indexed merge sort or Fenwick tree |
| Reverse Pairs, LC 493 | Modified merge sort |
| Count of Range Sum, LC 327 | Prefix sums plus merge counting |
| Maximum Profit in Job Scheduling, LC 1235 | Sort plus binary search and DP |
| Median from Data Stream, LC 295 | Two heaps |
| Smallest Range Covering K Lists, LC 632 | K-way heap merge |

## 15. Correctness and Edge Cases

### Loop invariants worth stating

| Algorithm | Useful invariant |
|---|---|
| Bubble sort | The suffix after `end` is sorted and final |
| Selection sort | The prefix before `start` contains the smallest final values |
| Insertion sort | The prefix before `index` is sorted |
| Merge | The output contains the smallest consumed values in sorted order |
| Quicksort partition | Values before the boundary satisfy the pivot relation |
| Heap sort | The active prefix is a heap and the suffix is sorted and final |
| Dutch flag | Left is smaller, middle is equal, right is larger, and one region is unknown |

### Cases to test

```python
SORT_CASES = [
    [],
    [1],
    [1, 2, 3, 4],
    [4, 3, 2, 1],
    [2, 2, 2, 2],
    [3, -1, 0, -1, 5, 3],
]
```

For every general sorting implementation, verify:

* Output is nondecreasing
* Output has the same length as input
* Every value appears the same number of times
* Empty and single-element inputs work
* Duplicates and negative values work when supported
* Already sorted and reverse-sorted inputs do not expose worst-case recursion bugs

### Frequent mistakes

* Calling heap construction `O(n log n)` instead of `O(n)`
* Claiming quicksort is always `O(n log n)`
* Forgetting that common quicksort and heapsort implementations are unstable
* Advancing the scan pointer after swapping an unknown Dutch-flag value from the end
* Using counting sort when the value range is much larger than the input
* Using an unstable digit sort inside radix sort
* Returning the Hoare split as though it were the pivot's final position
* Overwriting unread values while merging arrays from the front
* Sorting all values when quickselect or a size-`k` heap is enough
* Writing a comparator that is not transitive
* Ignoring recursion depth in Python quicksort implementations

## 16. Interview Communication Template

Before coding, say:

1. "A full sort gives `O(n log n)`, but I will check whether the constraints allow a
   linear non-comparison sort or a partial selection."
2. "I need to know whether stability and in-place mutation matter."
3. "The input characteristic that drives my choice is ..."
4. "I will maintain this invariant: ..."
5. "I will test empty input, duplicates, negatives, sorted input, and reverse order."

After coding, state:

* Time and auxiliary-space complexity
* Whether the implementation is stable and in-place
* Worst-case behavior and how pivot or distribution assumptions affect it
* One alternative and the constraint under which it becomes preferable

## 17. Practice Progression

### Phase 1: Implement from memory

1. Insertion sort
2. Merge sort
3. Randomized quicksort
4. Three-way partition
5. Heapsort
6. Counting sort
7. Radix sort

For each implementation, explain its invariant, stability, space usage, and worst
case without referring to notes.

### Phase 2: Master transformations

1. Merge sorted arrays and linked lists
2. Sort then scan intervals
3. Sort plus two pointers
4. Custom tuple keys and comparators
5. K-way merge with a heap
6. Count during merge sort
7. Quickselect and top `k`
8. Cyclic index placement
9. Dutch National Flag partitioning

### Phase 3: Timed interview set

1. Sort Colors in 15 minutes
2. Merge Intervals in 20 minutes
3. Kth Largest Element in 25 minutes
4. Sort List in 30 minutes
5. Largest Number in 30 minutes
6. Reverse Pairs in 40 minutes
7. First Missing Positive in 35 minutes

The goal is not to memorize every line. Build a small set of reusable invariants:
sorted prefix, sorted suffix, partition boundaries, heap root, and merge frontier.