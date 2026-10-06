"""The cache key of the agent economy's hidden spin-up years: the setup the years start from and the
source that runs them. Part of the port."""
import dataclasses
import hashlib
import json
import os

from . import solve_cache

# The spin-up runs the port's year module and, through it, the economy package; the interface never loads.
SPIN_UP_SOURCE_MODULES = ("sim.engine.economy_port_year",)


def _plain(value):
    """JSON-able content of `value`: objects by what they hold, paths in the checkout relative to it."""
    if isinstance(value, str):
        inside = value.startswith(solve_cache._ROOT + os.sep)
        return os.path.relpath(value, solve_cache._ROOT) if inside else value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(item) for item in value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if hasattr(value, "__dict__") and not isinstance(value, type) and vars(value):
        # underscore attributes are caches derived from the public content (a map's route tables), not content
        return {"type": type(value).__qualname__,
                "content": {name: _plain(item) for name, item in vars(value).items() if not name.startswith("_")}}
    # A repr would carry the object's address, giving a key no other process can ever hit.
    raise TypeError("cannot key the spin-up on a %s" % type(value).__name__)


def setup_digest(setup):
    """A stable digest of every field of an EconomySetup, however deeply nested."""
    text = json.dumps(_plain(setup), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def spin_up_key(setup):
    """The cache key of the spun-up record for `setup`: its digest, with the data files and the source
    the spin-up can run."""
    return solve_cache.solve_key({"agent_economy_spin_up": setup_digest(setup)},
                                 source_modules=SPIN_UP_SOURCE_MODULES)
