"""What the UI remembers about one game beyond the engine's save: player notes, extra goals, programmes.

Each feature asks `remembered(sim, topic)` for its own JSON-shaped dict and never sees where it is
kept. It lives in memory beside the `Sim` and is written into the save's session sidecar under one
key, until the save carries a slot the UI owns (Complaint 419). `save_state` and `load_state` here
wrap the engine's, so every save the UI makes carries the memory with it, forks included.
"""
import copy
import weakref

from sim.engine.ui_port import (
    load_state as engine_load_state, save_state as engine_save_state, settings)

SIDECAR_KEY = "interface"
_MEMORY = weakref.WeakKeyDictionary()  # sim -> {topic: JSON-shaped dict}


def remembered(sim, topic):
    """The dict this topic keeps for this game, created empty on first use. Values must be JSON data."""
    return _MEMORY.setdefault(sim, {}).setdefault(topic, {})


def snapshot(sim):
    return copy.deepcopy(_MEMORY.get(sim, {}))


def restore(sim, memory):
    _MEMORY[sim] = copy.deepcopy(memory or {})


def merge_session_meta(path, fields):
    """Write `fields` into the save's sidecar without dropping what other writers keep there."""
    meta = dict(settings.load_session_meta(path))
    meta.update(fields)
    return settings.save_session_meta(path, meta)


def _holds_something(value):
    """False for a topic that reads created but nothing filled: only empty containers inside."""
    if isinstance(value, dict):
        return any(_holds_something(inner) for inner in value.values())
    if isinstance(value, list):
        return bool(value)
    return value is not None


def save_state(sim, path):
    engine_save_state(sim, path)
    memory = {topic: kept for topic, kept in (_MEMORY.get(sim) or {}).items() if _holds_something(kept)}
    meta = dict(settings.load_session_meta(path))
    if not memory and SIDECAR_KEY not in meta:
        return
    if memory:
        meta[SIDECAR_KEY] = memory
    else:
        meta.pop(SIDECAR_KEY)
    settings.save_session_meta(path, meta)


def load_state(sim, path):
    engine_load_state(sim, path)
    memory = settings.load_session_meta(path).get(SIDECAR_KEY)
    restore(sim, memory if isinstance(memory, dict) else {})
