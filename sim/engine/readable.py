"""Marks the engine methods a data file may call with no arguments to read a number (figure paths in data/ui)."""


def readable(method):
    """Decorator: `method` only reads state, so a declared state path may call it."""
    method.ui_readable = True
    return method


def is_readable(method):
    return getattr(method, "ui_readable", False) is True
