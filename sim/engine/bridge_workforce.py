"""Bridge entries the workforce module reads until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old
labour adapter did, and is never cached. The `legacy_*` views are raw state the module still reads or writes in place;
they go when that state moves."""
from sim.assembly.api import KEYED, QUOTE

from . import data, units_prose, view_share, wage_schedule

from .bridge import bridge_view


# ---- the game's data -------------------------------------------------------------------------------------------------

@bridge_view("starting_wages")
def starting_wages(sim):
    """{trade: money an hour pays} on the reference civilisation's opening schedule."""
    return data.WAGES


@bridge_view("trades_absent")
def trades_absent(sim):
    """The trades that do not exist until someone teaches them."""
    return data.TRADES_ABSENT


@bridge_view("trade_notes")
def trade_notes(sim):
    """{trade: the explanatory note of the trade}."""
    return data.TRADE_NOTES


@bridge_view("trade_records")
def trade_records(sim):
    """{trade: the trade registry's record (family, training years, the rest of its file)}."""
    return data.TRADE_REGISTRY


@bridge_view("trade_family", kind=KEYED)
def trade_family(sim, trade):
    return data.trade_family(trade)


@bridge_view("wage_schedule_for", kind=QUOTE)
def wage_schedule_for(sim, civ, tightness_factors=None):
    """The wage schedule a civilisation opens on, built from the trade registry and the price solver."""
    return wage_schedule.build_schedule(data.TRADE_REGISTRY, civ, tightness_factors=tightness_factors)


@bridge_view("plain_number", kind=QUOTE)
def plain_number(sim, value, digits=0):
    """A count, a number of people or of hours, written for a sentence."""
    return units_prose.plain_number(value, digits)


@bridge_view("opening_wage_index")
def opening_wage_index(sim):
    """The wage index of the civilisation's opening year, which the index is measured against."""
    return sim._wage_index_base


@bridge_view("game_config")
def game_config(sim):
    return sim.cfg


@bridge_view("legacy_state")
def legacy_state(sim):
    """The game's saved state, whose seat sections labour still reads and writes in place."""
    return sim.state


# ---- the founder, the acting seat's land and the owner map ----------------------------------------------------------------


@bridge_view("farm_ladder")
def farm_ladder(sim):
    return sim._farm_ladder


@bridge_view("farm_arable_ceiling")
def farm_arable_ceiling(sim):
    return sim._farm_arable_ceiling


# ---- the actors and the agent economy ----------------------------------------------------------------------------------------

@bridge_view("teaching_knowledge")
def teaching_knowledge(sim):
    """(nodes held by each active actor, what the society already knows, what has been demonstrated)."""
    registry = getattr(sim, "actors", None)
    by_actor = {actor.identity(): set(actor.knowledge) for actor in (registry.actors.values() if registry is not None else ())
                if actor.record.exited_year is None}
    return by_actor, set(sim.state.projects.granted), sim.view("actor_world")().demonstrated()


@bridge_view("harvest_share_taken", kind=KEYED)
def harvest_share_taken(sim, material):
    """Share of the harvest of a material the home state's forms take from growers; none without a government."""
    from sim.agents.api import tax_burden
    if sim.view("cast")().government_of(None) is None:
        return 0.0
    return tax_burden.harvest_share_taken(sim.view("actor_world")(), material)


@bridge_view("concern_rows_stopped", kind=QUOTE)
def concern_rows_stopped(sim, node_ids):
    """The yearly value of the concerns among `node_ids` that stand stopped."""
    rows = sim.ledger_concern_rows()
    return sum(rows.get(node_id, 0.0) for node_id in node_ids)


@bridge_view("shared_answer", kind=QUOTE)
def shared_answer(sim, key, inputs, compute, standalone=False):
    """`compute()` reused while the engine's world stamp and `inputs` hold."""
    return view_share.of(sim)._shared_answer(key, inputs, compute, standalone)


