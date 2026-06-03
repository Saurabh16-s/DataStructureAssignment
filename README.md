Problem 1 — LRU Cache


Why HashMap + Doubly Linked List?
The core challenge is satisfying two O(1) requirements simultaneously: look up a value by key, and track usage order so we can evict the least-recently-used item. Neither structure alone is sufficient:

A hash map gives O(1) lookup but has no concept of order.
A singly linked list can track order but removing an arbitrary node requires O(n) traversal to find its predecessor.

A doubly linked list solves the removal problem — each node holds a pointer to both neighbours, so removing it is a constant-time pointer swap. The hash map maps every key directly to its node pointer, so we can jump to any node in O(1) without traversal. Two sentinel (dummy) nodes at the head and tail eliminate all edge-case checks for empty/single-element lists.


Problem 2 — min_rooms_required logic


Sort all start times and all end times independently. Then simulate a single sweep through start times. For each new event about to begin, ask: "has any previously started event already finished?" We check this by peeking at the smallest end time seen so far. If that end time ≤ the current start, one room has freed up — we don't need a new one. Otherwise we open a new room. The peak room count across all starts is the answer.
This works because we don't care which specific meeting ended — just whether one ended. Sorting end times gives us the earliest possible release in O(1) per query.

Final Discussion
Trade-offs of HashMap + DLL for LRU:
AspectHashMap + DLLAlternativesget/putO(1)Array: O(n) for shiftMemory2× overhead (pointers)OrderedDict (Python built-in, same internals)ImplementationMore complexSimpler with Python's collections.OrderedDict
Python's collections.OrderedDict is actually backed by the same structure internally — but implementing it manually demonstrates you understand why it works.
Thread safety for LRU Cache:
The ThreadSafeLRUCache in the file wraps every method with a threading.RLock. A few notes on the trade-offs:

A single coarse-grained lock serialises everything — safe, but a bottleneck under high concurrency.
A read-write lock (rwlock package) allows concurrent reads and exclusive writes — better throughput when reads dominate.
For very high-scale systems (e.g. distributed caches), you'd shard the cache into N independent LRU caches each with their own lock, reducing lock contention by ~N×.

Future-proofing the scheduler for named rooms:
Replace the two-pointer approach in min_rooms_required with a min-heap of (end_time, room_name). When a new event starts, pop from the heap if the earliest end time ≤ start — that gives you the specific room being freed. Push (new_end_time, recycled_room) back. If no room is free, generate the next label (Room A, Room B, …) and push it. This is exactly what assign_rooms() in the file does — same O(n log n) complexity, now with full room identity tracking.
