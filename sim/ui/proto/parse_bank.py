"""Typed-line parsing for found: 'found bank <capital>'."""
from . import typed


def parse_found(command, rest, words, nums, want_json):
    if not rest:
        return None, "found what? 'found bank <capital>' founds a bank."
    parsed = {"cmd": "found", "what": str(rest[0]).lower()}
    if len(rest) > 1:
        try:
            parsed["capital"] = float(str(rest[1]).replace(",", ""))
        except ValueError:
            return None, "the capital is an amount of money."
    return parsed, None


typed._COMMAND_PARSERS.setdefault("found", parse_found)
