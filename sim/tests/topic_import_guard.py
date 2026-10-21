"""Keeps a topic's module-level checks from running anywhere but in that topic.

A topic module runs its checks as it is imported, and some topics import helpers from another topic module.
Left alone, the importer would run (and count) the other topic's checks, and the other topic would then find its
module already imported and run nothing, so the total depended on which topics shared a process.
"""
import contextlib
import importlib.abc
import sys

from sim.tests import harness

TOPIC_PREFIX = "sim.tests.test_"
_LOADED_AS_HELPER = set()
_ACTIVE = []    # guards entered and not yet left; only the innermost one acts


class _MutedLoader(importlib.abc.Loader):
    """Runs a helper topic's module with check() silenced, so only its definitions arrive."""

    def __init__(self, inner):
        self.inner = inner

    def create_module(self, spec):
        return self.inner.create_module(spec)

    def exec_module(self, module):
        _LOADED_AS_HELPER.add(module.__name__)
        harness.MUTED[0] += 1
        try:
            self.inner.exec_module(module)
        finally:
            harness.MUTED[0] -= 1


class _HelperTopicFinder(importlib.abc.MetaPathFinder):
    def __init__(self, own_name):
        self.own_name = own_name

    def find_spec(self, name, path, target=None):
        if self is not _ACTIVE[-1] or not name.startswith(TOPIC_PREFIX) or name == self.own_name:
            return None
        for other in sys.meta_path:
            if isinstance(other, _HelperTopicFinder):
                continue
            spec = other.find_spec(name, path, target) if hasattr(other, "find_spec") else None
            if spec is not None:
                if spec.loader is not None:
                    spec.loader = _MutedLoader(spec.loader)
                return spec
        return None


@contextlib.contextmanager
def own_checks_only(own_name):
    """Within the block, `own_name` runs its checks and any other topic module imported is loaded silent.

    A module loaded earlier as another topic's helper is dropped, so its own checks run on import."""
    if own_name in _LOADED_AS_HELPER:
        _LOADED_AS_HELPER.discard(own_name)
        sys.modules.pop(own_name, None)
    finder = _HelperTopicFinder(own_name)
    sys.meta_path.insert(0, finder)
    _ACTIVE.append(finder)
    try:
        yield
    finally:
        _ACTIVE.remove(finder)
        sys.meta_path.remove(finder)
