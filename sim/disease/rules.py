"""The disease module's rules as plain functions of their inputs."""
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

# below this share of working-age people dead, a seat notices nothing
EPIDEMIC_NOTICE_SHARE = 0.002


def people_by_tile(held: Sequence[str], stored_regions: Optional[Mapping[str, Sequence[float]]], stored_ids: Sequence[str],
                   bands: Sequence[str], national: Mapping[str, float], shares_of_held) -> Dict[str, Dict[str, float]]:
    """{tile: {band: people}} over the tiles held: the regions the engine tracks once they cover the tiles (`stored_ids`
    is the held tiles' ids, sorted), else the nation's bands shared by each tile's share of the land's food
    (`shares_of_held()` is called only then)."""
    if stored_regions and sorted(stored_regions) == list(stored_ids):
        return {tile: dict(zip(bands, stored_regions[tile])) for tile in held}
    shares = shares_of_held()
    return {tile: {band: national[band] * shares.get(tile, 0.0) for band in bands} for tile in held}


def regional_loss(endemic_working_age: float, expected_by_tile: Mapping[str, Mapping[str, float]],
                  expected_working_age_share: float, people: Mapping[str, Mapping[str, float]], tile: str) -> float:
    """The share of a working-age person on `tile` the diseases there take in a year: the endemic rate plus the forecast
    deaths on the tile over its working-age people (the nation's expected share on a tile it does not hold)."""
    if tile in people:
        working_age = people[tile]["working_age"]
        killed = expected_by_tile.get(tile, {}).get("working_age", 0.0)
        epidemic = killed / working_age if working_age > 0.0 else 0.0
    else:
        epidemic = expected_working_age_share
    return min(1.0, endemic_working_age + epidemic)


def frontier_tiles(held: Iterable[str], borders: Mapping[str, Iterable[str]]) -> List[str]:
    """The sorted tiles held that border a tile not held."""
    held_set = set(held)
    return [tile for tile in sorted(held_set) if any(other not in held_set for other in borders.get(tile, ()))]


def seat_loss_report(name: str, share: float, people_before: float, cash_lost: float, cash_text: str) -> Tuple[str, bool]:
    """(the log line, whether the epidemic took nothing from the seat) for a seat cut by `share` of its working-age."""
    parts = ["staff -%d%%" % round(share * 100)] if people_before > 0.05 else []
    if cash_lost > 0.5:
        parts.append("%s of takings lost while the trade stood idle" % cash_text)
    text = "%s: %s. Empire-wide, %d%% of working-age people died" % (
        name, ", ".join(parts) or "you had nothing it could take", round(share * 100))
    return text, not parts
