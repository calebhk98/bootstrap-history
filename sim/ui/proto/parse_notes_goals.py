"""Typed-line parsers for note, notes and goals, joined to the typed parser's table on import."""
from . import typed


def _parse_note(command, rest, words, nums, want_json):
    return {"cmd": "note", "text": " ".join(str(word) for word in rest)}, None


def _parse_notes(command, rest, words, nums, want_json):
    out = {"cmd": "notes"}
    project_words = []
    for word in rest:
        key, _, value = str(word).partition(":")
        if key.lower() in ("limit", "offset") and value.isdigit():
            out[key.lower()] = int(value)
        elif key.lower() == "project" and value:
            project_words.append(value)
        else:
            project_words.append(str(word))
    if project_words:
        out["project"] = " ".join(project_words)
    return out, None


def _parse_goals(command, rest, words, nums, want_json):
    if rest and str(rest[0]).lower() in ("watch", "unwatch"):
        return {"cmd": "goals", "action": str(rest[0]).lower(), "goal": " ".join(rest[1:])}, None
    return {"cmd": "goals"}, None


for _name, _parser in (("note", _parse_note), ("notes", _parse_notes), ("goals", _parse_goals)):
    typed._COMMAND_PARSERS.setdefault(_name, _parser)
