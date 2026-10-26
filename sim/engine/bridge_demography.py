"""Bridge entries the demography module reads and sends until the owners behind them move into modules.

Each view carries the name its owner will publish, asks the engine exactly as the old code did, and is never cached. Each
command applies what the yearly demographic step did inline, in the same order."""
from sim.actors.api import RecordMigrantContact, ScaleStrata
from sim.assembly.api import QUOTE
from sim.land.api import AdvanceColonies

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
