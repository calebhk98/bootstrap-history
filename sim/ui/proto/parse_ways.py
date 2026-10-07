"""Typed-line parsing for build_way: `build_way road <tile> <tile> [preview]`."""
from . import typed


def parse_build_way(command, rest, words, nums, want_json):
    preview = any(str(word).lower() in ("preview", "dry_run") for word in rest)
    names = [str(word) for word in rest if str(word).lower() not in ("preview", "dry_run", "to", "from")]
    if len(names) != 3:
        return None, "build_way takes a way and two tiles: build_way road <tile> <tile>"
    out = {"cmd": "build_way", "way": names[0].lower(), "from": names[1], "to": names[2]}
    if preview:
        out["preview"] = True
    return out, None


typed._COMMAND_PARSERS.setdefault("build_way", parse_build_way)
