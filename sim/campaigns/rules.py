"""Campaign rules as plain functions of plain values. The world rules (battle, supply, the march) are in
`sim/world/campaign_*.py`; these are the ones the module's records and orders need."""
from typing import Any, Dict, List, Optional

from sim.agents.api import unrest
from sim.geography.api import settlement
from sim.refusal import Refusal
from sim.world import campaign_year_rules
from sim.world.army_record import Army


def army_id(number: int) -> str:
	return "army_%d" % number


def own_army(records: Dict[str, Dict[str, Any]], owner: str, army_id_asked: Any) -> Any:
	"""The owner's army of this id, or a Refusal."""
	record = records.get(army_id_asked)
	if record is None:
		return Refusal("unknown_army", "no army %r. Nothing was changed." % (army_id_asked,),
		               sorted(key for key, other in records.items() if other["owner"] == owner))
	if record["owner"] != owner:
		return Refusal("not_your_army", "army %s is not yours. Nothing was changed." % army_id_asked)
	return Army.from_dict(record)


def order(army: Army, tile: str) -> None:
	"""Put the army under an order to `tile` (none when it already stands there), its progress on the road cleared."""
	army.target, army.progress_days = (None if tile == army.tile else tile), 0.0


def recall_tile(home_tile: str, home_tile_owner: Optional[str], owner: str, owned_tiles: List[str]) -> Optional[str]:
	"""Where a recalled army goes: its home tile while that is still the owner's, else the owner's best-endowed tile."""
	home = home_tile if home_tile_owner == owner else None
	return home or (settlement.default_base_tile(owned_tiles) if owned_tiles else None)


def keep_within_force(records: Dict[str, Dict[str, Any]], owners: List[str], force_of: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
	"""An army is a slice of the state's force: when a state keeps fewer soldiers than its armies hold, they are stood
	down by the same share (scaled in place). Returns the records of armies still of a soldier or more."""
	for owner in owners:
		fielded = sum(float(record["soldiers"]) for record in records.values() if record["owner"] == owner)
		share = campaign_year_rules.share_of_force_kept(fielded, force_of[owner])
		if share < 1.0:
			for record in records.values():
				if record["owner"] == owner:
					campaign_year_rules.scale_army_record(record, share)
	return {army_id_kept: record for army_id_kept, record in records.items() if record["soldiers"] >= 1.0}


def state_grievance(taxpayer_income: float, wage_per_year: float, hours_per_year: float, corvee_hours: float,
                    revenue_taken: float, dole_need: float, dole_unfunded: float, unfunded: float) -> Optional[float]:
	"""What the state took (taxes, levies) and owes beyond what it gave (the dole), over its taxpayers' income; None while
	no taxpayer income is visible."""
	if taxpayer_income <= 0.0:
		return None
	levy = corvee_hours / hours_per_year * wage_per_year if hours_per_year > 0.0 else 0.0
	taken = revenue_taken + levy
	given = max(0.0, dole_need - dole_unfunded)
	return unrest.grievance(taken, unfunded, given, taxpayer_income)
