"""The cache key of the agent economy's hidden spin-up years: the setup the years start from and the
source that runs them. Part of the port."""
import dataclasses
import hashlib
import json
import os
import types

from . import solve_cache

# The spin-up runs the port's year module and, through it, the economy package; the interface never loads.
SPIN_UP_SOURCE_MODULES = ("sim.engine.economy_port_year",)


KEY_FLOAT_DIGITS = 12


def _plain(value, ancestors=()):
    """JSON-able content of `value`: objects by what they hold, paths in the checkout relative to it.
    An object's `_` attributes are memos built from the rest (the map's route rates) and are left out;
    a cycle through what is left is refused."""
    if isinstance(value, str):
        inside = value.startswith(solve_cache._ROOT + os.sep)
        return os.path.relpath(value, solve_cache._ROOT) if inside else value
    if isinstance(value, float):
        return float("%.*g" % (KEY_FLOAT_DIGITS, value))    # a last-place difference (a coin's scale) is not a different setup
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, types.FunctionType):
        return "%s.%s" % (value.__module__, value.__qualname__)    # a rule handed in; its source is in the key's closure
    if any(value is ancestor for ancestor in ancestors):
        raise TypeError("cannot key the spin-up on a %s that contains itself" % type(value).__name__)
    ancestors = ancestors + (value,)
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {field.name: _plain(getattr(value, field.name), ancestors) for field in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(key): _plain(item, ancestors) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item, ancestors) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(item, ancestors) for item in value)
    if hasattr(value, "__dict__") and not isinstance(value, type) and vars(value):
        return {"type": type(value).__qualname__,
                "content": {name: _plain(item, ancestors) for name, item in vars(value).items()
                            if not name.startswith("_")}}
    # A repr would carry the object's address, giving a key no other process can ever hit.
    raise TypeError("cannot key the spin-up on a %s" % type(value).__name__)


def setup_digest(setup):
    """A stable digest of every field of an EconomySetup, however deeply nested."""
    text = json.dumps(_plain(setup), sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _counted_in_units(setup):
    """The setup with the coin set aside: the economy counts money in its own unit and never reads the coin
    (only the port converts to it), so games that differ only in their coin share a spin-up."""
    if dataclasses.is_dataclass(setup) and any(field.name == "coin_per_unit" for field in dataclasses.fields(setup)):
        return dataclasses.replace(setup, coin_per_unit=1.0)
    return setup


def spin_up_key(setup, years=None):
    """The cache key of the spun-up record for `setup`: its digest, with the data files and the source
    the spin-up can run, and the spin-up's years when they are not the declared ones."""
    inputs = {"agent_economy_spin_up": setup_digest(_counted_in_units(setup))}
    if years is not None:
        inputs["years"] = list(years)
    return solve_cache.solve_key(inputs, source_modules=SPIN_UP_SOURCE_MODULES)
