"""How much of a resource's output sits on each tile, from the named deposits that stand on it.

A deposit row carries a position and a share of the reference civilisation's output of its resource:
`share_of_empire_output` for a deposit inside that empire (it also drives the supply curve of
sim/world/deposits.py), `share_of_reference_output` for any other district. A resource is tracked when some
row of it carries the second field; gold and mercury, whose rows carry only the first, are not. Position
resolves to the tile holding it, so a share is stored once, on a deposit, and a region is only a label.
Standalone: reads data files only, never the engine.
"""
from typing import Any, Dict, Iterable, List, Optional, Set

from sim.constants import declare
from sim.geography import tile_lookup
from sim.geography.queries import deposit_records

REFERENCE_SHARE_KEY = "share_of_reference_output"
EMPIRE_SHARE_KEY = "share_of_empire_output"

Rows = List[Dict[str, Any]]


def _declare_reference_share(row: Dict[str, Any]) -> None:
    name = "DEPOSIT_REFERENCE_SHARE_%s" % row["id"].upper()
    declare(name, row[REFERENCE_SHARE_KEY], kind="temporary_heuristic",
            unit="fraction of the reference civilisation's output of %s (dimensionless)" % row["resource"],
            source=row.get("source"), confidence=row.get("conf", "D"),
            why="No district-level production series is read for %s, so the share is the rough relative "
                "abundance the former region table gave, sited at this named district; replace with the "
                "district's production or reserves relative to the reference output." % row["name"])


def share_rows(rows: Optional[Rows] = None) -> Rows:
    """The catalogue rows that carry a share of output, each with its share under `share`."""
    rows = rows if rows is not None else deposit_records()
    kept = []
    for row in rows:
        key = REFERENCE_SHARE_KEY if REFERENCE_SHARE_KEY in row else EMPIRE_SHARE_KEY
        if key in row:
            if key == REFERENCE_SHARE_KEY:
                _declare_reference_share(row)
            kept.append(dict(row, share=row[key]))
    return kept


def tracked_resources(rows: Optional[Rows] = None) -> Set[str]:
    """Resources whose output is shared out over tiles: those with a row on the reference-share field."""
    return {row["resource"] for row in (rows if rows is not None else deposit_records())
            if REFERENCE_SHARE_KEY in row}


def deposit_shares_by_tile(geography: Dict[str, Any], rows: Optional[Rows] = None) -> Dict[str, Dict[str, float]]:
    """{resource: {tile_id: share of output}} for the tracked resources, each deposit on the tile that holds it."""
    rows = rows if rows is not None else deposit_records()
    tracked = tracked_resources(rows)
    tiles = geography.get("land_tiles", {}).get("tiles", {})
    by_resource: Dict[str, Dict[str, float]] = {}
    for row in share_rows(rows):
        if row["resource"] in tracked:
            tile_id = tile_lookup.nearest_tile_id(tiles, row["lat"], row["lon"])
            on_tile = by_resource.setdefault(row["resource"], {})
            on_tile[tile_id] = on_tile.get(tile_id, 0.0) + row["share"]
    return by_resource


def held_share(held_tiles: Iterable[str], resource: str, geography: Dict[str, Any],
               rows: Optional[Rows] = None) -> float:
    """Share of a resource's output on the tiles held: the deposits sitting on them. An untracked resource
    gives zero."""
    held = set(held_tiles)
    return sum(share for tile_id, share in deposit_shares_by_tile(geography, rows).get(resource, {}).items()
               if tile_id in held)
