"""Typed-line parsing for settle: `settle` lists the tiles, `settle <tile>` founds a colony."""
from . import typed


def parse_settle(command, rest, words, nums, want_json):
    names = [str(word) for word in rest if str(word).lower() != "on"]
    return ({"cmd": "settle", "tile": names[0]} if names else {"cmd": "settle"}), None


typed._COMMAND_PARSERS.setdefault("settle", parse_settle)
