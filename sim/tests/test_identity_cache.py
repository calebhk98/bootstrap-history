"""identity_cache: a cache keyed by an object's address cannot return another object's entry.

Complaints/303. `id()` is only unique among live objects, so an address-keyed cache
that does not confirm the hit replays a stale result under a recycled address. The
cache class confirms every hit with `is`, and engine code keys on an address nowhere else.
"""
import ast
import os

from .harness import *  # noqa: F401,F403
from .harness import ROOT
from sim.engine.identity_cache import IdentityCache

_cache = IdentityCache()
_first = {"tree": 1}
_cache.put(_first, "first result")
check("a cache returns the entry stored for the same object", _cache.get(_first) == "first result")
check("a different object is a miss", _cache.get({"tree": 1}) is None)
check("a miss returns the caller's default", _cache.get({}, "none") == "none")

# a recycled address: an entry stored for an old object, looked up with a new one at its address
_new = {"tree": 2}
_cache._entries[id(_new)] = ({"tree": "old object"}, "stale result")
check("an entry for another object at the same address is a miss", _cache.get(_new) is None)

_cache.clear()
check("clear drops every entry", _cache.get(_first) is None and len(_cache) == 0)

# no engine module keys a dictionary on an address except through the cache class
_outside = []
_engine_root = os.path.join(ROOT, "sim", "engine")
for _dirpath, _dirnames, _filenames in os.walk(_engine_root):
    _dirnames[:] = [name for name in _dirnames if name != "__pycache__"]
    for _filename in sorted(_filenames):
        if not _filename.endswith(".py") or _filename == "identity_cache.py":
            continue
        _path = os.path.join(_dirpath, _filename)
        for _node in ast.walk(ast.parse(open(_path).read())):
            if (isinstance(_node, ast.Call) and isinstance(_node.func, ast.Name)
                    and _node.func.id == "id"):
                _outside.append("%s:%d" % (os.path.relpath(_path, ROOT), _node.lineno))
check("engine code calls id() only inside IdentityCache", not _outside, _outside)
