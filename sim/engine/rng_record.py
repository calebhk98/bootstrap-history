"""A game's dice as a save carries them: the generator's state as plain JSON data, and the way back."""


def rng_record(rng):
    """[version, keys, gaussian] of a `random.Random`, or None when it cannot say."""
    try:
        version, keys, gaussian = rng.getstate()
        return [version, list(keys), gaussian]
    except Exception:
        return None


def restore_rng(rng, record):
    """Put a record from `rng_record` back, so the dice go on from where they stopped."""
    version, keys, gaussian = record
    rng.setstate((version, tuple(int(key) for key in keys), gaussian))
