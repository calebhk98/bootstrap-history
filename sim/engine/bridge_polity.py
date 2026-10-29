"""Bridge entries the polity module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code did, and
is never cached. The `legacy_*` views are raw state or the engine's own objects the module still needs; they go when that state
moves: the household's purse and facade, and the constants `Sim` still declares (`legacy_constant`)."""
from sim.assembly.api import KEYED

from . import need_substitutes
from .bridge import bridge_view


@bridge_view("danger_lines")
def danger_lines(sim):
	"""The eminence and suspicion figures past which a household is in danger."""
	return {"eminence": sim.cfg["eminence_danger"], "suspicion": sim.cfg["suspicion_danger"]}


# ---- actors ----------------------------------------------------------------------------------------------------------------

# ---- the ledger ------------------------------------------------------------------------------------------------------------

@bridge_view("legacy_household_actor", seat_scoped=True)
def legacy_household_actor(sim):
	"""The acting seat's household as an actor (the facade a payment names)."""
	return sim.household


# ---- projects and the household's versions ---------------------------------------------------------------------------------

@bridge_view("held_and_running_versions", seat_scoped=True)
def held_and_running_versions(sim):
	"""(the version of the techniques held, the version of those running) of the acting seat: what a memo is keyed by."""
	return sim.household.done_version, sim.household.operating_version


# ---- production, workforce, materials -------------------------------------------------------------------------------------

@bridge_view("material_substitutes", kind=KEYED)
def material_substitutes(sim, material):
	"""The materials that serve a need `material` serves."""
	return need_substitutes.substitutes_of(material)
