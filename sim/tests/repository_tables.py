"""The trade and technology tables of the repository's own mods, for tests that hold no game (a game answers from its own mods)."""
from sim.content.api import load_tech_effects, trade_notes, trade_registry, trades_absent
from sim.engine.data import MODDIR, schedule_of_civilisation
from sim.labour.api import wage_provider

TRADE_REGISTRY = trade_registry(MODDIR)
TRADE_NOTES = trade_notes(TRADE_REGISTRY)
TRADES_ABSENT = trades_absent(TRADE_REGISTRY)
TRADE_FAMILY = {trade_id: trade.family for trade_id, trade in TRADE_REGISTRY.items()}
TECH_EFFECTS = load_tech_effects(MODDIR)
STARTING_SCHEDULE = schedule_of_civilisation(wage_provider.reference_civilisation())
WAGES = STARTING_SCHEDULE.wages_per_hour()
ANNUAL_WAGE = {trade: STARTING_SCHEDULE.annual_wage(trade) for trade in WAGES}


def trade_family(trade):
    return TRADE_FAMILY.get(trade, "craft")


def production_catalog():
    """The production entries of the repository's mods, as a game over them hands them out."""
    from sim.world.demand import production_data
    return production_data(MODDIR)


def tonnes_per_unit(material):
    from sim.markets.unit_mass import tonnes_per_unit as tonnes
    return tonnes(material, production_catalog())
