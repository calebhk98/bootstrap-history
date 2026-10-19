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

    def tile_owner_version(self):
        """Changes whenever who owns a tile does (a transfer, or a replaced owner map)."""
        return (self.__dict__.get("_tile_transfers", 0), id(self.tile_owner_map()))

    def _owned_tiles_memo(self):
        """{actor: sorted tiles} and the home country's held tiles, rebuilt only when the owner map is replaced
        or `transfer_tile` has changed it."""
        owners = self.tile_owner_map()
        memo = self.__dict__.get("_owned_tiles")
        key = (self.__dict__.get("_tile_transfers", 0), str(self.civ.get("id")), self.world_map)
        if memo is None or memo["owners"] is not owners or memo["key"] != key:
            by_actor = {}
            for tile_id, entry in sorted(owners.items()):
                by_actor.setdefault(entry["owner"], []).append(tile_id)
            memo = {"owners": owners, "key": key, "by_actor": by_actor, "home": None}
            self.__dict__["_owned_tiles"] = memo
        return memo

    def tiles_owned_by(self, actor_id):
        """Sorted tiles this country or seat owns, at any control level."""
        return list(self._owned_tiles_memo()["by_actor"].get(actor_id, ()))

    def home_tiles_held(self):
        """The tiles the home country owns."""
        memo = self._owned_tiles_memo()
        if memo["home"] is None:
            memo["home"] = tiles_held(self.civ, self.world_map, memo["owners"])
        return list(memo["home"])

    def transfer_tile(self, tile_id, to_actor, control=None, cause="transfer"):
        """Give a tile to a country or seat (None releases it); returns the previous owner. Writes the change to
        the world event log with its cause."""
        controls = self.stores.view("control")
        self.__dict__["_tile_transfers"] = self.__dict__.get("_tile_transfers", 0) + 1
        previous = tile_owners.transfer(self.tile_owner_map(), tile_id, to_actor, control, self.world_map, controls)
        world_events.record(self, "tile_transfer", actors=[actor for actor in (previous, to_actor) if actor],
                            tiles=[tile_id], cause=cause, from_owner=previous, to_owner=to_actor,
                            control=tile_owners.control_of(controls, tile_id))
        return previous

    def way_owners(self):
        """{key: owner or None} of every built way, read from who owns the tiles it stands on."""
        owners = self.tile_owner_map()
        return {key: tile_owners.way_owner(owners, key) for key in self.state.economy.improvements}
