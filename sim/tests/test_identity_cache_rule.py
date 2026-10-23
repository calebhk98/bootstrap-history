"""identity_cache: a cache keyed by an object's address cannot return another object's entry (Complaints/303). `id()` is
only unique among live objects, so the cache class confirms every hit with `is`."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.identity_cache import IdentityCache

_cache = IdentityCache()
_first = {"tree": 1}
_cache.put(_first, "first result")
# not text: the cache's stored value
check("a cache returns the entry stored for the same object", _cache.get(_first) == "first result")
check("a different object is a miss", _cache.get({"tree": 1}) is None)
check("a miss returns the caller's default", _cache.get({}, "none") == "none")

# a recycled address: an entry stored for an old object, looked up with a new one at its address
_new = {"tree": 2}
_cache._entries[id(_new)] = ({"tree": "old object"}, "stale result")
check("an entry for another object at the same address is a miss", _cache.get(_new) is None)

_cache.clear()
check("clear drops every entry", _cache.get(_first) is None and len(_cache) == 0)
