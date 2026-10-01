"""A cache keyed by an object's identity that cannot hand back another object's entry.

`id()` is only unique among live objects, so a freed object's address can be given to
the next allocation. Each entry here keeps the key object itself alive and every lookup
confirms it with `is`, so a recycled address is a miss, never a stale hit.
"""


class IdentityCache:
    """Maps a key object (by identity, not equality) to a value."""

    def __init__(self):
        self._entries = {}

    def get(self, key_object, default=None):
        entry = self._entries.get(id(key_object))
        if entry is not None and entry[0] is key_object:
            return entry[1]
        return default

    def put(self, key_object, value):
        self._entries[id(key_object)] = (key_object, value)

    def clear(self):
        self._entries.clear()

    def __len__(self):
        return len(self._entries)
