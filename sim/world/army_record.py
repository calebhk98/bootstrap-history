"""An army: a located body of soldiers owned by an actor, with the equipment it carries, the food it holds, the
pay it is owed and the order it is under. Plain data; every rule that moves, feeds, wears down or fights it is a
function in `campaign_*.py` or `battle.py`. The owner is any actor that owns tiles (a country or a seat)."""
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Army:
    army_id: str
    owner: str
    tile: str
    soldiers: float
    equipment_kg: float                 # worked iron and ammunition one soldier is supplied with in a year
    food_kg: float = 0.0                # grain the army carries
    animals: float = 0.0                # pack animals of its baggage train
    supply_state: float = 1.0           # share of its food need met in the last stretch of days
    pay_owed: float = 0.0               # money the owner owes it, in the owner's coin
    target: Optional[str] = None        # the tile it is ordered to; None when it holds where it stands
    progress_days: float = 0.0          # days already marched toward the next tile on its way
    home_tile: str = ""                 # the tile it was raised at, where it falls back to
    raised_year: int = 0
    log: List[Dict[str, Any]] = field(default_factory=list)   # this year's events, for the owner's report

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(record: Dict[str, Any]) -> "Army":
        return Army(**record)


def fielded_soldiers(armies: Dict[str, Dict[str, Any]], owner: str) -> float:
    """Soldiers of `owner` now in the field, over every army record it has."""
    return sum(float(record["soldiers"]) for record in armies.values() if record["owner"] == owner)
