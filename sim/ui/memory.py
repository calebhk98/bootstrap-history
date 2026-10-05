"""What the UI remembers about one game beyond the engine's save: player notes, extra goals, programmes.

Each feature asks `remembered(sim, topic)` for its own JSON-shaped dict and never sees where it is
kept. It lives in the save's `interface` slot, which the engine carries and never reads, so every
save, load and fork carries it. The schema inside belongs to the UI.
"""
import copy

from sim.engine.ui_port import (
    interface_memory, load_state, save_state, set_interface_memory, settings)  # noqa: F401


def remembered(sim, topic):
    """The dict this topic keeps for this game, created empty on first use. Values must be JSON data."""
    return interface_memory(sim).setdefault(topic, {})


def snapshot(sim):
    return copy.deepcopy(interface_memory(sim))


def restore(sim, memory):
    set_interface_memory(sim, copy.deepcopy(memory or {}))


def merge_session_meta(path, fields):
    """Write `fields` into the save's sidecar without dropping what other writers keep there."""
    meta = dict(settings.load_session_meta(path))
    meta.update(fields)
    return settings.save_session_meta(path, meta)
