"""The money an hour of work was worth when the tree's money fields were counted, kept beside a save.

The opening counts the tree's money fields at the economy's wage as the game opens, and later
figures replace it only when the society's techs change. A game built to load a save does not open
its economy (that is what makes loading slow), so it takes the figure from this note. The note names
the game by a fingerprint of its stored opening; a missing or foreign note means the game must be
built the long way."""
import hashlib
import json

NOTE_SUFFIX = ".nodes_price.txt"


def _fingerprint(state):
    opening = state.economy.agent_economy.get("opening")
    if opening is None:
        return None
    return hashlib.sha256(json.dumps(opening, sort_keys=True, default=str).encode()).hexdigest()


def note_path(path):
    return path + NOTE_SUFFIX


def write_note(sim, path):
    """Record the figure the live tree is counted at, unless the note already says so."""
    figure = getattr(sim, "nodes_money_per_labour_hour", None)
    fingerprint = _fingerprint(sim.state)
    if figure is None or fingerprint is None:
        return
    text = json.dumps({"fingerprint": fingerprint, "money_per_labour_hour": figure})
    target = note_path(path)
    try:
        with open(target, encoding="utf-8") as handle:
            if handle.read() == text:
                return
    except OSError:
        pass
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(text)
    except OSError:
        pass


def noted_figure(path, state):
    """The noted money per labour hour for the loaded game, or None when there is no note for this game."""
    try:
        with open(note_path(path), encoding="utf-8") as handle:
            note = json.load(handle)
        if note["fingerprint"] == _fingerprint(state):
            return float(note["money_per_labour_hour"])
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None
