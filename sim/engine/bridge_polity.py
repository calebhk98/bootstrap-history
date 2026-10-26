"""Bridge entries the polity module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code did, and
is never cached. The `legacy_*` views are raw state or the engine's own objects the module still needs; they go when that state
moves: the actors (`legacy_actor_registry`, `legacy_actors_state`, `state_treasury`) and the household's purse and facade."""
from sim.assembly.api import KEYED

from . import need_substitutes
from .bridge import bridge_view


# ---- core: the game ----------------------------------------------------------------------------------------------

@bridge_view("legacy_game")
def legacy_game(sim):
	"""The game itself: a mod's wealth-claim readers and seizers (sim.polity.api.register_wealth_claims) take it."""
	return sim


@bridge_view("danger_lines")
def danger_lines(sim):
	"""The eminence and suspicion figures past which a household is in danger."""
	return {"eminence": sim.cfg["eminence_danger"], "suspicion": sim.cfg["suspicion_danger"]}


# ---- actors ----------------------------------------------------------------------------------------------------------------

@bridge_view("legacy_actors_state")
def legacy_actors_state(sim):
	"""The cast's saved state, or None before any actor exists (reading it never makes one)."""
	return sim.state.actors


@bridge_view("state_treasury", seat_scoped=True)
def state_treasury(sim):
	"""The government actor of the acting seat's country (the object itself)."""
	return sim.state_treasury()


# ---- the ledger ------------------------------------------------------------------------------------------------------------

@bridge_view("legacy_household_actor", seat_scoped=True)
def legacy_household_actor(sim):
	"""The acting seat's household as an actor (the facade a payment names)."""
	return sim.household


# ---- projects and the household's versions ---------------------------------------------------------------------------------

@bridge_view("standing_floor", seat_scoped=True)
def standing_floor(sim):
	"""The reputation the acting seat keeps for what it has built, whatever else happens."""
	return sim.standing_floor()


@bridge_view("rep_factor", seat_scoped=True)
def rep_factor(sim):
	"""How much easier reputation makes everything: 1.0 at zero reputation."""
	return sim.rep_factor()


@bridge_view("legacy_done_versions", seat_scoped=True)
def legacy_done_versions(sim):
	"""(the version of the techniques held, the version of those running) of the acting seat: what a memo is keyed by."""
	return sim.household.done_version, sim.household.operating_version


# ---- production, workforce, materials -------------------------------------------------------------------------------------

@bridge_view("concern_revenue", kind=KEYED, seat_scoped=True)
def concern_revenue(sim, node_id):
	"""What a running concern of the acting seat takes in a year."""
	return sim.concern_revenue(node_id)


@bridge_view("material_substitutes", kind=KEYED)
def material_substitutes(sim, material):
	"""The materials that serve a need `material` serves."""
	return need_substitutes.substitutes_of(material)
