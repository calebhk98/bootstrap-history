"""identity_cache (source lint; the cache class itself is in test_identity_cache_rule): a cache keyed by an object's address cannot return another object's entry.

Complaints/303. `id()` is only unique among live objects, so an address-keyed cache
that does not confirm the hit replays a stale result under a recycled address. The
cache class confirms every hit with `is`, and engine code keys on an address nowhere else.
"""
import ast
import os

from .harness import *  # noqa: F401,F403
from .harness import ROOT

# no engine module keys a dictionary on an address except through the cache class
_outside = []
from .source_dirs import engine_side_dirs
for _dirpath, _dirnames, _filenames in (_entry for _directory in engine_side_dirs() for _entry in os.walk(_directory)):
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
