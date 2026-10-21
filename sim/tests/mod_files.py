"""Load a shipped mod's Python file as a module, and run its `register` against a recording stand-in for `ModCodeApi`."""
import importlib.util
import os
import types

from sim.engine.data import ROOT


def load_mod_file(mod_id, name):
    path = os.path.join(ROOT, "mods", mod_id, name)
    spec = importlib.util.spec_from_file_location("test_mod_%s_%s" % (mod_id, os.path.splitext(name)[0]), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordingApi:
    """Records what `register` asks of the mod API; `state` is a plain dict per mod."""

    def __init__(self, mod_id):
        self.mod_id = mod_id
        self.calls = []
        self.memory = {}

    def __getattr__(self, name):
        def record(*args, **fields):
            self.calls.append((name, args, fields))
            return lambda handler: handler
        return record

    def registered(self, name):
        return [call for call in self.calls if call[0] == name]

    def state(self, memory):
        return self.memory

    def command(self, name, **fields):
        self.calls.append(("command", (name,), fields))
        return lambda handler: handler

    def director_overhead(self, function):
        self.calls.append(("director_overhead", (function,), {}))
        return function

    def town_provider(self, name, function):
        self.calls.append(("town_provider", (name, function), {}))

    effects = types.SimpleNamespace()
