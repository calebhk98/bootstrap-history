"""Bridge entries the demography module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached. Each
command applies what the yearly demographic step did inline, in the same order."""
from sim.actors.api import RecordMigrantContact, ScaleStrata
from sim.assembly.api import QUOTE
from sim.land.api import AdvanceColonies
from sim.workforce.api import AllocateFarmWorkforce, ApplyLandClearing, UpdateWages

from . import contact_events, externalities, mod_effects
from .bridge import bridge_command, bridge_view


# ---- land ----

@bridge_view("borders_among", kind=QUOTE)
def borders_among(sim, tiles):
    """{tile: the tiles it borders} for each of the tiles on the map."""
    return sim.geography.borders_among(tiles)


@bridge_command(AdvanceColonies)
def advance_colonies(sim, command):
    sim.advance_colonies(command.year)


# ---- workforce ----

@bridge_view("town_mortality_premium_by_tile")
def town_mortality_premium_by_tile(sim):
    """{tile: premium} for the tiles whose town carries a mortality premium from a registered provider (a share of the
    baseline death rate); empty with no provider."""
    return sim.labour.town_mortality_premium_by_tile()


@bridge_view("wage_index_terms")
def wage_index_terms(sim):
    """What the wage index is measured against: the base year's index and how much scarcer labour raises its own price."""
    return {"base": sim._wage_index_base, "elasticity": sim.WAGE_SCARCITY_ELASTICITY}


@bridge_command(AllocateFarmWorkforce)
def allocate_farm_workforce(sim, command):
    return sim.labour.allocate_farm_workforce(command.adult_equivalent_population)


@bridge_command(ApplyLandClearing)
def apply_land_clearing(sim, command):
    sim.labour.apply_land_clearing()


@bridge_command(UpdateWages)
def update_wages(sim, command):
    sim.labour.update_wages()


# ---- agriculture: the farm land and the year's technique, which the farm workforce keeps on the engine ----

@bridge_view("farm_land")
def farm_land(sim):
    """The land the farm holds and its quality (the farm workforce sets it as it clears ground)."""
    return sim.farm_land


@bridge_view("farm_technique_this_year")
def farm_technique_this_year(sim):
    """The farming technique the farm workforce chose for the year."""
    return sim._farm_technique_this_year


# ---- the mods' externalities and the actors ----

@bridge_view("externality_deaths", kind=QUOTE)
def externality_deaths(sim, deaths_by_band, year):
    """`deaths_by_band` plus what the mods' externalities add to the year's deaths."""
    return externalities.add_deaths(deaths_by_band, sim, year)


@bridge_command(RecordMigrantContact)
def record_migrant_contact(sim, command):
    contact_events.after_migration(sim, command.pairs)


@bridge_command(ScaleStrata)
def scale_strata(sim, command):
    for actor in mod_effects.strata_of(sim, command.country):
        actor.record.members *= 1.0 - command.share
