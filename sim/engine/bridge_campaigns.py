"""Bridge entries the campaigns module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the entry
is deleted. Each command is applied the way the old campaign code did the write."""
from sim.assembly.api import KEYED
from sim.stores.api import WriteStore

from .bridge import bridge_command, bridge_view


# ---- actors and the states ----

@bridge_view("has_state", kind=KEYED)
def has_state(sim, owner):
    """Whether the owner is a country with a state (a seat's colony or a bare owner has no soldiers to raise)."""
    return owner == str(sim.civ["id"]) or owner in sim.view("cast")().state.countries


@bridge_view("countries")
def countries(sim):
    return list(sim.view("cast")().state.countries)


@bridge_view("organised_factions", kind=KEYED)
def organised_factions(sim, owner):
    """[(members, grievance)] of the organised interest groups of the owner."""
    home = str(sim.civ["id"])
    return [(group.record.members, group.record.grievance) for group in sim.view("cast")().of_kind("interest_group")
            if group.organised() and (group.record.country or home) == owner]


@bridge_view("store", kind=KEYED)
def store(sim, name):
    """A declared store as it stands: {default, values: {key: value}}."""
    declared = sim.stores.view(name)
    return {"default": declared.spec.default, "values": dict(declared.values)}


# ---- commands of owners that have not moved ----


@bridge_command(WriteStore)
def write_store(sim, command):
    sim.stores.write(command.store, command.key, command.value, command.owner)


