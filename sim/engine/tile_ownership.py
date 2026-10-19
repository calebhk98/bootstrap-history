"""Who owns each tile of the map, saved in `state.economy.tile_owners` (sim/geography/tile_owners.py).

Seeded from the civilisation files of the home country and the partners inside the agent economy the first
time it is read; every later change goes through `transfer_tile`, whoever the actor is.
"""
from sim.geography.api import tile_owners, tiles_held

from . import world_events


class TileOwnershipMixin:

    def tile_owner_map(self):
        """{tile: {owner, control}}, seeded from the civilisation files on first use."""
        economy = self.state.economy
        if not economy.tile_owners:
            from .data import load_civ
            claims = {self.civ["id"]: tiles_held(self.civ, self.world_map)}
            for partner in self.partners_in_agent_economy():
                claims[partner] = tiles_held(load_civ(partner), self.world_map)
            economy.tile_owners, economy.tile_claim_conflicts = tile_owners.seed(claims)
            tile_owners.seed_controls(economy.tile_owners, self.stores.view("control"))
        return economy.tile_owners

    def tile_owner(self, tile_id):
        return tile_owners.owner_of(self.tile_owner_map(), tile_id)

    def tile_control(self, tile_id):
        self.tile_owner_map()   # seeds the owners and their control levels on first use
        return tile_owners.control_of(self.stores.view("control"), tile_id)

    def tiles_owned_by(self, actor_id):
        """Sorted tiles this country or seat owns, at any control level."""
        return tile_owners.tiles_of(self.tile_owner_map(), actor_id)

    def home_tiles_held(self):
        """The tiles the home country owns."""
        return tiles_held(self.civ, self.world_map, self.tile_owner_map())

    def transfer_tile(self, tile_id, to_actor, control=None, cause="transfer"):
        """Give a tile to a country or seat (None releases it); returns the previous owner. Writes the change to
        the world event log with its cause."""
        controls = self.stores.view("control")
        previous = tile_owners.transfer(self.tile_owner_map(), tile_id, to_actor, control, self.world_map, controls)
        world_events.record(self, "tile_transfer", actors=[actor for actor in (previous, to_actor) if actor],
                            tiles=[tile_id], cause=cause, from_owner=previous, to_owner=to_actor,
                            control=tile_owners.control_of(controls, tile_id))
        return previous

    def way_owners(self):
        """{key: owner or None} of every built way, read from who owns the tiles it stands on."""
        owners = self.tile_owner_map()
        return {key: tile_owners.way_owner(owners, key) for key in self.state.economy.improvements}
