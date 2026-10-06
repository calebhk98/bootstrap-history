"""The cache key of the agent economy's hidden spin-up years: the setup the years start from and the
source that runs them. Part of the port."""
import dataclasses
import hashlib
import json

from . import solve_cache

# The spin-up runs the port's year module and, through it, the economy package; the interface never loads.
SPIN_UP_SOURCE_MODULES = ("sim.engine.economy_port_year",)


def _plain(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(item) for item in value)
    return value if value is None or isinstance(value, (bool, int, float, str)) else repr(value)


def setup_digest(setup):
    """A stable digest of every field of an EconomySetup, however deeply nested."""
    text = json.dumps(_plain(setup), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def spin_up_key(setup):
    """The cache key of the spun-up record for `setup`: its digest, with the data files and the source
    the spin-up can run."""
    return solve_cache.solve_key({"agent_economy_spin_up": setup_digest(setup)},
                                 source_modules=SPIN_UP_SOURCE_MODULES)
