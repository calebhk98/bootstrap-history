"""What a seat may deal in: it deals as any actor does, limited to what moves cleanly between a seat and an actor."""
from typing import Any, Dict, List, Optional

SEAT_DEALT_KEYS = ("money", "patent", "licence", "royalty", "shares")


def unsupported_kinds(side: Dict[str, Any]) -> List[str]:
    """The kinds in one side of an offer that a seat does not deal in, sorted."""
    return sorted(set(side) - set(SEAT_DEALT_KEYS))


def unsupported_reason(side: Dict[str, Any]) -> Optional[str]:
    """Why a seat cannot deal in this side of an offer, or None when it can."""
    extra = unsupported_kinds(side)
    if extra:
        return "a seat deals in money, patents, licences, royalties and shares, not %s" % ", ".join(extra)
    return None
