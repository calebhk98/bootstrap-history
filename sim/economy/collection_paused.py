"""Cyclic garbage collection stands still while a year runs: the year frees nearly everything by reference
count, and each collection would walk a heap of every record, order and memo the year holds."""
import contextlib
import gc


@contextlib.contextmanager
def collection_paused():
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if was_enabled:
            gc.enable()
