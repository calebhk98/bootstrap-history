"""Bridge entries the campaigns module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the entry
is deleted. Each command is applied the way the old campaign code did the write."""
from sim.actors.api import RecordConquestContact
from sim.agents import api as agents_api
from sim.assembly.api import KEYED, QUOTE
from sim.demography.api import AddCaptives
from sim.geography.api import (endemic_people_loss, food_potential, layer_value, reach, route, usable_modes)
from sim.land.api import TransferTile
from sim.stores.api import WriteStore

from . import contact_events
from .bridge import bridge_command, bridge_view


def _country_world(sim, owner):
    from .agents_port import SimWorld
    return sim.actors.world_of_country(owner, SimWorld(sim))


# ---- land ----

@bridge_view("tile_owner_map")
def tile_owner_map(sim):
    """{tile: {owner, control}}, seeded from the civilisation files on first use."""
    return sim.tile_owner_map()


@bridge_view("tile_facts", kind=KEYED)
def tile_facts(sim, tile):
    """What a tile gives an army, from the map: the food it can feed, the working-age people its endemic disease takes in a
    year, and its ruggedness; None for a tile not on the map. Static, so kept per tile."""
    if tile not in sim.world_map.tiles:
        return None
    cache = sim.__dict__.setdefault("_campaign_sites", {})
    if tile not in cache:
        cache[tile] = (float(food_potential(tile, world_map=sim.world_map)["total_kcal_per_year"]),
                       float(endemic_people_loss([tile], sim.world_map).get("working_age", 0.0)),
                       float(layer_value(tile, "ruggedness_index", sim.world_map) or 0.0))
    food, disease, ruggedness = cache[tile]
    return {"food_kcal_per_year": food, "working_age_endemic_loss": disease, "ruggedness": ruggedness}


@bridge_view("home_modes")
def home_modes(sim):
    """The ways the home country's goods can travel: what its built ways and ports allow."""
    return list(usable_modes([sim.held_and_running()], sim.world_map))


@bridge_view("route_between", kind=QUOTE)
def route_between(sim, origin, target, modes):
    """The fastest route from one tile to another by these modes over the built ways, or None."""
    return route([origin], [target], modes, sim.state.economy.improvements, held_nodes=sim.held_and_running(),
                 world_map=sim.world_map, fastest=True)


@bridge_view("reach_from", kind=QUOTE)
def reach_from(sim, tile, modes, range_days):
    """{tile: days} reachable from a tile by these modes within `range_days`."""
    return reach([tile], modes, range_days, sim.state.economy.improvements, world_map=sim.world_map)


# ---- actors and the states ----

@bridge_view("has_state", kind=KEYED)
def has_state(sim, owner):
    """Whether the owner is a country with a state (a seat's colony or a bare owner has no soldiers to raise)."""
    return owner == str(sim.civ["id"]) or owner in sim.actors.state.countries


@bridge_view("country_world", kind=KEYED)
def country_world(sim, owner):
    """The world the owner's state sees (the shared one for the home country, else its country's scope)."""
    return _country_world(sim, owner)


@bridge_view("countries")
def countries(sim):
    return list(sim.actors.state.countries)


@bridge_view("organised_factions", kind=KEYED)
def organised_factions(sim, owner):
    """[(members, grievance)] of the organised interest groups of the owner."""
    home = str(sim.civ["id"])
    return [(group.record.members, group.record.grievance) for group in sim.actors.of_kind("interest_group")
            if group.organised() and (group.record.country or home) == owner]


@bridge_view("played_countries")
def played_countries(sim):
    """The countries a seat plays."""
    return sorted({seat.country or str(sim.civ["id"]) for seat in sim.state.seats.values()
                   if getattr(seat, "kind", None) == "country"})


@bridge_view("food_eaten")
def food_eaten(sim):
    """{tile: share of the people's food need the tile's people ate}."""
    return sim.state.population.regional_eaten_over_need


@bridge_view("store", kind=KEYED)
def store(sim, name):
    """A declared store as it stands: {default, values: {key: value}}."""
    declared = sim.stores.view(name)
    return {"default": declared.spec.default, "values": dict(declared.values)}


# ---- commands of owners that have not moved ----

@bridge_command(TransferTile)
def transfer_tile(sim, command):
    return sim.transfer_tile(command.tile, command.to_actor, command.control, cause=command.cause)


@bridge_command(WriteStore)
def write_store(sim, command):
    sim.stores.write(command.store, command.key, command.value, command.owner)


@bridge_command(RecordConquestContact)
def record_conquest_contact(sim, command):
    contact_events.after_conquest(sim, command.conqueror, command.previous, command.tile)


@bridge_command(AddCaptives)
def add_captives(sim, command):
    return agents_api.add_captives(sim.actors, command.winner, command.people)

