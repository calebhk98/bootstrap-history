"""Raising armies from a state's soldiers, and the defence a state not played by anyone orders for itself.

An army in the field is a slice of the soldiers the state keeps (the army line of `budget.py`): it can never be
larger than that force, its dead are struck from it, and its pay owed is the state's arrears on the army line shared
out by head. Plain functions; the engine reads the records and hands numbers and ids in. Any actor that owns tiles
can raise and order an army, a seat as much as a country."""
from typing import Any, Dict, List, Optional, Tuple

from sim.refusal import Refusal


def available_soldiers(under_arms: float, fielded: float) -> float:
    """Soldiers of the state's force not yet in an army."""
    return max(0.0, under_arms - fielded)


def raise_refusal(requested: Any, available: float, tile_owner: Optional[str], owner: str,
                  known_tile: bool) -> Optional[Refusal]:
    """Why an army cannot be raised, or None: the number is not positive, there are not that many soldiers free, or
    the tile it is raised on is not the owner's."""
    if isinstance(requested, bool) or not isinstance(requested, (int, float)) or requested <= 0.0:
        return Refusal("army_size_not_positive", "an army needs a positive number of soldiers. Nothing was changed.",
                       None, requested=str(requested))
    if not known_tile:
        return Refusal("unknown_tile", "no such tile on the map. Nothing was changed.")
    if tile_owner != owner:
        return Refusal("tile_not_yours", "an army is raised on a tile you own. Nothing was changed.", None,
                       tile=str(tile_owner))
    if requested > available + 1e-9:
        return Refusal("not_enough_soldiers", "the state keeps %d soldiers not yet in an army. Nothing was changed."
                       % int(available), None, available=available, requested=requested)
    return None


def pay_owed_share(arrears_on_army: float, soldiers_kept: float, soldiers_in_army: float) -> float:
    """Money of the state's army arrears that falls to an army of `soldiers_in_army`, by head."""
    if soldiers_kept <= 0.0:
        return 0.0
    return max(0.0, arrears_on_army) * min(1.0, soldiers_in_army / soldiers_kept)


def pay_owed_years(pay_owed: float, soldiers: float, pay_per_soldier_year: float) -> float:
    """Years of its pay an army is owed."""
    if soldiers <= 0.0 or pay_per_soldier_year <= 0.0:
        return 0.0
    return max(0.0, pay_owed) / (soldiers * pay_per_soldier_year)


def struck_from_force(under_arms: float, killed: float) -> float:
    """The force a state keeps once its field armies' dead are struck from it."""
    return max(0.0, under_arms - max(0.0, killed))


def threats_to(owner: str, tile_owners: Dict[str, str], armies: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """{tile of `owner`: soldiers of other owners standing on it or ordered to it}: the tiles the state sees
    threatened, from armies in the world's record. A tile an unowned army merely stands on is no threat."""
    threatened: Dict[str, float] = {}
    for record in armies.values():
        if record["owner"] == owner:
            continue
        for tile in {record["tile"], record.get("target")}:
            if tile is not None and tile_owners.get(tile) == owner:
                threatened[tile] = threatened.get(tile, 0.0) + float(record["soldiers"])
    return threatened


def defence_orders(owner: str, tile_owners: Dict[str, str], armies: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    """[(army id, tile)] a state not played by anyone orders: each of its free armies (none ordered) to the tile
    threatened most that is not already covered by one of its armies, the largest army to the largest threat. No
    other policy: such a state never attacks."""
    threatened = threats_to(owner, tile_owners, armies)
    mine = sorted((record for record in armies.values() if record["owner"] == owner),
                  key=lambda record: (-float(record["soldiers"]), record["army_id"]))
    covered = {record["tile"] for record in mine if record["tile"] in threatened}
    open_tiles = sorted((tile for tile in threatened if tile not in covered), key=lambda tile: (-threatened[tile], tile))
    orders: List[Tuple[str, str]] = []
    for record in mine:
        if not open_tiles:
            break
        if record["tile"] in threatened:
            continue
        orders.append((record["army_id"], open_tiles.pop(0)))
    return orders


def defence_musters(owner: str, tile_owners: Dict[str, str], armies: Dict[str, Dict[str, Any]],
                    free_soldiers: float) -> List[Tuple[str, float]]:
    """[(tile, soldiers)] a state not played by anyone raises on its threatened tiles that none of its armies stands
    on, the largest threat first, each as many soldiers as the threat has (fewer when the state keeps no more free)."""
    threatened = threats_to(owner, tile_owners, armies)
    covered = {record["tile"] for record in armies.values() if record["owner"] == owner}
    musters: List[Tuple[str, float]] = []
    for tile in sorted((tile for tile in threatened if tile not in covered), key=lambda tile: (-threatened[tile], tile)):
        sent = min(free_soldiers, threatened[tile])
        if sent <= 0.0:
            break
        musters.append((tile, sent))
        free_soldiers -= sent
    return musters
