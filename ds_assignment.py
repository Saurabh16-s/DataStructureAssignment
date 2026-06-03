"""
Data Structures & Systems Design — SE Intern Assessment
Author: Saurabh
"""

# ─────────────────────────────────────────────────────────────
# PROBLEM 1: LRU Cache
# ─────────────────────────────────────────────────────────────
#
# APPROACH (plain English):
# The key constraint is O(1) for both get and put. A plain dict gives
# O(1) lookup, but evicting the "least recently used" item requires
# knowing the usage ORDER — which a dict alone can't track efficiently.
#
# The classic solution: pair a hash map with a doubly linked list.
#   - The doubly linked list maintains order from most→least recently used.
#     Moving a node to the front (on access) is O(1) IF we have a direct
#     pointer to it — no traversal needed.
#   - The hash map stores key → node pointer, giving us that direct
#     pointer in O(1).
#
# Two sentinel nodes (head, tail) act as dummy boundaries so we never
# have to do null/edge-case checks when inserting or removing nodes.
#
# On get: find the node via the map, move it to the front, return value.
# On put: if key exists, update and move to front. If new and at capacity,
#         remove the node just before the tail (= LRU), delete its map
#         entry, then insert the new node at the front.

import threading
import heapq


class _Node:
    __slots__ = ("key", "val", "prev", "next")

    def __init__(self, key=0, val=0):
        self.key = key
        self.val = val
        self.prev = None
        self.next = None


class LRUCache:
    """
    O(1) get and put using a hash map + doubly linked list.
    Most-recently-used node sits right after head sentinel.
    Least-recently-used node sits right before tail sentinel.
    """

    def __init__(self, capacity: int):
        if capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")
        self.capacity = capacity
        self.map: dict[int, _Node] = {}

        # Sentinel nodes — never hold real data
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    # ── internal helpers ──────────────────────────────────────

    def _remove(self, node: _Node) -> None:
        """Unlink a node from wherever it is in the list."""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _insert_front(self, node: _Node) -> None:
        """Insert a node immediately after the head sentinel (= MRU position)."""
        node.next = self.head.next
        node.prev = self.head
        self.head.next.prev = node
        self.head.next = node

    # ── public API ────────────────────────────────────────────

    def get(self, key: int) -> int:
        if key not in self.map:
            return -1
        node = self.map[key]
        self._remove(node)
        self._insert_front(node)
        return node.val

    def put(self, key: int, value: int) -> None:
        if key in self.map:
            node = self.map[key]
            node.val = value
            self._remove(node)
            self._insert_front(node)
        else:
            if len(self.map) == self.capacity:
                # LRU node is just before the tail sentinel
                lru = self.tail.prev
                self._remove(lru)
                del self.map[lru.key]
            new_node = _Node(key, value)
            self.map[key] = new_node
            self._insert_front(new_node)

    def __repr__(self) -> str:
        items, node = [], self.head.next
        while node is not self.tail:
            items.append(f"{node.key}:{node.val}")
            node = node.next
        return f"LRUCache([{' → '.join(items)}], cap={self.capacity})"


# ── Thread-safe wrapper (bonus / discussion question) ─────────

class ThreadSafeLRUCache(LRUCache):
    """
    Wraps every public method with a reentrant lock so the cache is safe
    for concurrent reads and writes from multiple threads.

    Trade-off: a single lock serialises all operations. For very high
    throughput you'd consider finer-grained locking (e.g. per-shard) or
    a read-write lock (threading.RWLock via rwlock package) that allows
    concurrent reads when no write is in progress.
    """

    def __init__(self, capacity: int):
        super().__init__(capacity)
        self._lock = threading.RLock()

    def get(self, key: int) -> int:
        with self._lock:
            return super().get(key)

    def put(self, key: int, value: int) -> None:
        with self._lock:
            super().put(key, value)


# ─────────────────────────────────────────────────────────────
# PROBLEM 2: Event Scheduler
# ─────────────────────────────────────────────────────────────
#
# APPROACH — can_attend_all (plain English):
#   Sort events by start time. Walk through them in order. If the next
#   event starts BEFORE the previous one ends (strict less-than, because
#   adjacent end==start is NOT an overlap per the spec), we have a
#   conflict → return False immediately.
#
# APPROACH — min_rooms_required (plain English):
#   Think of this as a "meeting room" problem. At any moment, the number
#   of rooms needed equals the number of events currently in progress.
#
#   We simulate time by creating two sorted lists:
#     • start times (sorted ascending)
#     • end times   (sorted ascending)
#
#   Walk through start times one by one. For each new event starting:
#     - If the earliest-ending active event has ALREADY ended
#       (end ≤ new start), that room is free — reuse it (advance end pointer).
#     - Otherwise, open a new room.
#   The maximum rooms open at any point is the answer.
#
#   Why this works: we don't care WHICH meeting ends, only WHETHER any
#   meeting has ended. Sorting end times and using a pointer is a
#   min-heap simulation in O(n log n) time.
#
# FUTURE-PROOFING — room assignment:
#   Replace the end-time pointer with a min-heap of (end_time, room_name).
#   When a room frees up, pop its name from the heap and recycle it.
#   When a new room is needed, generate the next label ("Room A", "Room B"…)
#   and push it onto the heap when the event ends.
#   See assign_rooms() below for the full implementation.


class EventScheduler:

    @staticmethod
    def can_attend_all(events: list[tuple[int, int]]) -> bool:
        """
        Returns True if no two events overlap.
        Adjacent events (end == start) are allowed.

        Time:  O(n log n) — dominated by sorting
        Space: O(n) — sorted copy (or O(log n) with in-place sort on a copy)
        """
        if len(events) < 2:
            return True
        sorted_events = sorted(events, key=lambda e: e[0])
        for i in range(1, len(sorted_events)):
            # Strict overlap: next starts BEFORE previous ends
            if sorted_events[i][0] < sorted_events[i - 1][1]:
                return False
        return True

    @staticmethod
    def min_rooms_required(events: list[tuple[int, int]]) -> int:
        """
        Returns the minimum number of rooms needed to host all events.

        Time:  O(n log n) — sorting
        Space: O(n) — two auxiliary sorted lists
        """
        if not events:
            return 0

        starts = sorted(e[0] for e in events)
        ends   = sorted(e[1] for e in events)

        rooms = 0
        max_rooms = 0
        end_ptr = 0

        for start in starts:
            if ends[end_ptr] <= start:
                # A room has freed up — reuse it
                end_ptr += 1
            else:
                # No room free — open a new one
                rooms += 1
            max_rooms = max(max_rooms, rooms)

        # Total rooms = rooms we opened (never decremented above, so max_rooms
        # IS the peak. Alternatively track directly:)
        return rooms  # equals max_rooms at the final iteration

    @staticmethod
    def assign_rooms(
        events: list[tuple[int, int]]
    ) -> list[tuple[tuple[int, int], str]]:
        """
        Assigns a named room ("Room A", "Room B", …) to each event.

        Returns a list of ((start, end), room_name) pairs, sorted by start.

        Uses a min-heap keyed on (end_time, room_name) so we can always
        find the earliest-freeing room in O(log n).

        Time:  O(n log n)
        Space: O(n)
        """
        if not events:
            return []

        sorted_events = sorted(events, key=lambda e: e[0])
        # Min-heap: (end_time, room_label)
        available: list[tuple[int, str]] = []
        room_counter = 0
        result: list[tuple[tuple[int, int], str]] = []

        def _next_room_label() -> str:
            nonlocal room_counter
            # A → Z, then AA, AB, … (simple bijective base-26)
            n, label = room_counter, ""
            while True:
                label = chr(ord("A") + n % 26) + label
                n = n // 26 - 1
                if n < 0:
                    break
            room_counter += 1
            return f"Room {label}"

        for event in sorted_events:
            start, end = event
            if available and available[0][0] <= start:
                # Recycle the earliest-freeing room
                _, room = heapq.heappop(available)
            else:
                room = _next_room_label()
            heapq.heappush(available, (end, room))
            result.append((event, room))

        return result


# ─────────────────────────────────────────────────────────────
# DEMO / SMOKE TESTS
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("PROBLEM 1 — LRU Cache")
    print("=" * 55)

    cache = LRUCache(2)
    cache.put(1, 1);  print(cache)          # [1:1]
    cache.put(2, 2);  print(cache)          # [2:2 → 1:1]
    print("get(1):", cache.get(1))          # 1  — now MRU
    print(cache)                            # [1:1 → 2:2]
    cache.put(3, 3)                         # evicts key 2 (LRU)
    print(cache)                            # [3:3 → 1:1]
    print("get(2):", cache.get(2))          # -1 (evicted)
    cache.put(4, 4)                         # evicts key 1
    print(cache)                            # [4:4 → 3:3]
    print("get(1):", cache.get(1))          # -1
    print("get(3):", cache.get(3))          # 3
    print("get(4):", cache.get(4))          # 4

    print("\n" + "=" * 55)
    print("PROBLEM 2 — Event Scheduler")
    print("=" * 55)

    s = EventScheduler()

    e1 = [(9, 10), (10, 11), (11, 12)]
    print(f"Events: {e1}")
    print(f"  can_attend_all  : {s.can_attend_all(e1)}")    # True
    print(f"  min_rooms       : {s.min_rooms_required(e1)}") # 1

    e2 = [(9, 11), (10, 12), (11, 13)]
    print(f"\nEvents: {e2}")
    print(f"  can_attend_all  : {s.can_attend_all(e2)}")    # False
    print(f"  min_rooms       : {s.min_rooms_required(e2)}") # 2

    e3 = [(9, 10), (9, 11), (9, 12)]
    print(f"\nEvents: {e3}")
    print(f"  can_attend_all  : {s.can_attend_all(e3)}")    # False
    print(f"  min_rooms       : {s.min_rooms_required(e3)}") # 3

    print("\n--- Room Assignment ---")
    assignments = s.assign_rooms(e2)
    for event, room in assignments:
        print(f"  {event} → {room}")

    assignments2 = s.assign_rooms(e3)
    for event, room in assignments2:
        print(f"  {event} → {room}")
