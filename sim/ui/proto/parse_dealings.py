"""Typed-line parsing for the dealings commands that take one word: patent <id>, accept <offer id>, decline <offer id>."""
from . import typed


def parse_patent(command, rest, words, nums, want_json):
    return ({"cmd": "patent", "id": " ".join(str(word) for word in rest)} if rest else {"cmd": "patent"}), None


def _parse_answer(command, rest, words, nums, want_json):
    if not rest:
        return None, "%s needs the id of an offer; 'offers' lists them." % command
    return {"cmd": command, "offer": str(rest[0])}, None


typed._COMMAND_PARSERS.setdefault("patent", parse_patent)
typed._COMMAND_PARSERS.setdefault("accept", _parse_answer)
typed._COMMAND_PARSERS.setdefault("decline", _parse_answer)
