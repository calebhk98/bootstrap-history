"""The game's version and the semantic-version comparison mods use."""
import re
from typing import Tuple

GAME_VERSION = "0.1.0"

_VERSION = re.compile(r"\d+(?:\.\d+){0,2}")
_COMPARATOR = re.compile(r"(>=|<=|==|>|<|=)\s*(\S+)")


def parse_version(text: str) -> Tuple[int, int, int]:
    """Parse `major[.minor[.patch]]`; a missing part is zero. Anything else raises ValueError."""
    text = str(text).strip()
    if not _VERSION.fullmatch(text):
        raise ValueError("%r is not a version like 1.2.3" % (text,))
    parts = [int(part) for part in text.split(".")]
    return tuple(parts + [0] * (3 - len(parts)))


def satisfies(version: str, version_range: str) -> bool:
    """True when `version` meets every comma-separated comparator of `version_range` (for example `>=1.2,<2`)."""
    found = parse_version(version)
    for clause in version_range.split(","):
        match = _COMPARATOR.fullmatch(clause.strip())
        if not match:
            raise ValueError("%r is not a version comparator like >=1.2" % (clause.strip(),))
        bound = parse_version(match.group(2))
        operator = match.group(1)
        holds = {">=": found >= bound, "<=": found <= bound, ">": found > bound,
                 "<": found < bound, "==": found == bound, "=": found == bound}[operator]
        if not holds:
            return False
    return True
