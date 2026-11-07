"""Reads of a year view kept until the market memory is next written to, for a caller that prices many cohorts alike."""


def kept_reads(view, key, compute):
    """`compute()` once per `key` until the view's memory is written to; a view without kept reads computes every time.
    The result is shared by every caller of the key: callers read it and never change it."""
    current = getattr(view, "_current", None)
    if current is None:
        return compute()
    reads = current()
    try:
        return reads[key]
    except KeyError:
        found = reads[key] = compute()
        return found
