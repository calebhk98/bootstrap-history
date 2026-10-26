"""The rules the yearly campaign phase (`sim/campaigns/campaign_year.py`) applies between the larger world rules: what a march
costs in camp days, where losses are booked, how a force is shared out, when a withdrawn or
routed army goes home and when a taken tile rises in control. Plain functions of the values they are given."""
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from . import campaign_contest
from .army_record import Army

LOSS_CAUSES = ("hunger", "disease", "desertion")
SCALED_RECORD_FIELDS = ("soldiers", "food_kg", "animals", "pay_owed")


def march_camps(legs: Sequence[Tuple[str, float]], progress_days: float,
                days_left: float) -> Tuple[List[Tuple[str, float]], float, float]:
    """([(tile, days spent camped there)], progress into the next leg, days used): the tiles reached in the days the
    season leaves, then the days walked part-way into the next leg spent on the tile the army stands on."""
    steps, progress, used = campaign_contest.march(legs, progress_days, days_left)
    camps = list(steps)
    walked_between = used - sum(days for _, days in steps)
    if walked_between > 0.0:
        camps.append((None, walked_between))   # None: the tile the army is on after the last step
    return camps, progress, used


def book_losses(army: Army, result: Mapping[str, float], lost: Dict[str, float]) -> None:
    """Add this camp's hunger, disease and desertion to the owner's dead and log each cause that took a soldier."""
    for cause in LOSS_CAUSES:
        lost[army.owner] = lost.get(army.owner, 0.0) + result[cause]
        if result[cause] >= 1.0:
            army.log.append({"kind": cause, "tile": army.tile, "soldiers": round(result[cause])})


def share_of_force_kept(fielded: float, force: float) -> float:
    """The share of its armies a state keeps standing when they hold `fielded` soldiers and the force is `force`."""
    if fielded <= force + 1e-9:
        return 1.0
    return max(0.0, force) / fielded


def scale_army_record(record: Dict[str, Any], share: float) -> None:
    """Stand an army record down by `share`: men, grain, animals and the pay owed shrink together."""
    for key in SCALED_RECORD_FIELDS:
        record[key] *= share


def contest_action(result: str) -> Optional[str]:
    """What a siege's result does to the tile: 'take' it, 'withdraw' the attacker, or nothing while it continues."""
    if result in ("attacker_won", "defenders_gone"):
        return "take"
    if result in ("attacker_lost", "attacker_withdraws"):
        return "withdraw"
    return None


def garrison_strength(free_soldiers: float, population_share_of_tile: float) -> float:
    """The part of a state's soldiers not in an army that holds one tile: its people's share of the state's."""
    return free_soldiers * population_share_of_tile


def withdraw(army: Army, why: str, home_is_owners: bool, note: str = "withdrew") -> None:
    """The army gives up its order and, if the tile it was raised at is still its owner's, falls back to it."""
    army.log.append({"kind": note, "tile": army.tile, "why": why})
    army.target, army.progress_days = None, 0.0
    if home_is_owners:
        army.tile = army.home_tile


def rout(army: Army, home_is_owners: bool) -> bool:
    """A beaten defender falls back to its home tile if that is still its owner's and not this one; True when its
    men instead go home and the army is stood down."""
    if army.home_tile and army.home_tile != army.tile and home_is_owners:
        army.tile, army.target, army.progress_days = army.home_tile, None, 0.0
        return False
    return True


def conquest_entry(year: int, owner: str, previous_owner: Optional[str]) -> Dict[str, Any]:
    """The record of a tile taken: when, by whom and from whom."""
    return {"year": year, "by": owner, "from": previous_owner}


def consolidation(entry: Mapping[str, Any], current_owner: Optional[str], garrisoned: bool, year: int,
                  current_level: Optional[str], levels: Mapping[str, Mapping[str, Any]], level_after_years) -> Tuple[bool, Optional[str]]:
    """(keep the record, control level to set or None) for a tile taken: a tile that changed hands is forgotten; one
    its taker still holds with an army on it rises to the level its years held earn, never down."""
    if current_owner != entry["by"]:
        return False, None
    if not garrisoned:
        return True, None
    level = level_after_years(year - entry["year"])
    if levels[level]["rank"] > levels.get(current_level, {"rank": 0})["rank"]:
        return True, level
    return True, None
