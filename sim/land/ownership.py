"""Who holds each tile: the owner map, the control levels in the `control` store, and every change of hands.

The map is seeded from the civilisation files of the home country and the partners inside the agent economy the first
time it is read; every later change goes through `TransferTile`, whoever the actor is."""
from typing import Any, Dict, List, Optional

from sim.actors.api import FollowTileTransfer
from sim.geography.api import tile_owners, tiles_held
from sim.hazards.api import RecordWorldEvent
from sim.stores.api import WriteStore


class ControlStore:
    """The `control` tile store as the owner rules read and write it: writes are commands, reads are the store as it stands."""

    def __init__(self, needs: Any):
        self._needs = needs

    def get(self, tile: str) -> Optional[str]:
        stored = self._needs.store["control"]
        return stored["values"].get(tile, stored["default"])

    def set(self, tile: str, level: Optional[str]) -> None:
        self._needs.send(WriteStore("control", tile, level))


class ControlSnapshot:
    """The `control` store read once, for a loop over many tiles."""

    def __init__(self, needs: Any):
        stored = needs.store["control"]
        self._values, self._default = stored["values"], stored["default"]

    def get(self, tile: str) -> Optional[str]:
        return self._values.get(tile, self._default)


class Ownership:
    """Mixed into `Land`."""

    needs: Any
    world: Any

    def tile_owner_map(self) -> Dict[str, Dict[str, str]]:
        """{tile: {owner}}, seeded from the civilisation files on first use."""
        world = self.world
        if not world.tile_owners:
            civ = self.needs.civilisation()
            claims = {civ["id"]: tiles_held(civ, self.world_map)}
            for partner in self.needs.partners_in_agent_economy():
                claims[partner] = tiles_held(self.needs.civilisation_record[partner], self.world_map)
            world.tile_owners, world.tile_claim_conflicts = tile_owners.seed(claims)
            tile_owners.seed_controls(world.tile_owners, ControlStore(self.needs))
        return world.tile_owners

    def tile_owner(self, tile_id: str) -> Optional[str]:
        return tile_owners.owner_of(self.tile_owner_map(), tile_id)

    def tile_control(self, tile_id: str) -> Optional[str]:
        self.tile_owner_map()   # seeds the owners and their control levels on first use
        return tile_owners.control_of(ControlStore(self.needs), tile_id)

    def home_tiles_held_version(self) -> Any:
        """Changes whenever who owns a tile does (a transfer, or a replaced owner map)."""
        owners = self.tile_owner_map()
        seen = self._caches.get("owner_map_seen")
        if seen is None or seen[0] is not owners:
            seen = (owners, (seen[1] + 1) if seen else 0)
            self._caches["owner_map_seen"] = seen
        return (self._caches.get("transfers", 0), seen[1])

    def _owned_tiles_memo(self) -> Dict[str, Any]:
        """{actor: sorted tiles} and the home country's held tiles, rebuilt only when the owner map is replaced or a
        transfer has changed it."""
        owners = self.tile_owner_map()
        memo = self._caches.get("owned_tiles")
        key = (self._caches.get("transfers", 0), str(self.needs.civilisation().get("id")), self.world_map)
        if memo is None or memo["owners"] is not owners or memo["key"] != key:
            by_actor: Dict[Any, List[str]] = {}
            for tile_id, entry in sorted(owners.items()):
                by_actor.setdefault(entry["owner"], []).append(tile_id)
            memo = {"owners": owners, "key": key, "by_actor": by_actor, "home": None}
            self._caches["owned_tiles"] = memo
        return memo

    def tiles_owned_by(self, actor_id: Optional[str]) -> List[str]:
        """Sorted tiles this country or seat owns, at any control level."""
        return list(self._owned_tiles_memo()["by_actor"].get(actor_id, ()))

    def home_tiles_held(self) -> List[str]:
        """The tiles the home country owns."""
        memo = self._owned_tiles_memo()
        if memo["home"] is None:
            memo["home"] = tiles_held(self.needs.civilisation(), self.world_map, memo["owners"])
        return list(memo["home"])

    def transfer_tile(self, command: Any) -> Optional[str]:
        """Give a tile to a country or seat (None releases it); answers the previous owner. Writes the change to the world
        event log with its cause."""
        return self.hand_over(command.tile, command.to_actor, command.control, command.cause)

    def hand_over(self, tile_id: str, to_actor: Optional[str], control: Optional[str], cause: str) -> Optional[str]:
        controls = ControlStore(self.needs)
        self._caches["transfers"] = self._caches.get("transfers", 0) + 1
        previous = tile_owners.transfer(self.tile_owner_map(), tile_id, to_actor, control, self.world_map, controls)
        self.needs.send(FollowTileTransfer(tile_id, previous, to_actor))
        self.needs.send(RecordWorldEvent(
            "tile_transfer", actors=tuple(actor for actor in (previous, to_actor) if actor), tiles=(tile_id,), cause=cause,
            facts=dict(from_owner=previous, to_owner=to_actor, control=tile_owners.control_of(controls, tile_id))))
        return previous

    def claimed_tiles(self) -> List[str]:
        """Tiles some other actor owns (a seat's colony, a partner's land): a tile has one owner."""
        home = self.needs.civilisation()["id"]
        return [tile for tile, entry in self.tile_owner_map().items() if entry["owner"] != home]

    def tile_ownership_problems(self) -> List[Dict[str, Any]]:
        """What breaks the one-owner rule now: each {cause, tile, ...} (sim/geography/tile_owners.py)."""
        claims = {seat_id: [colony["tile"] for colony in self.seat_of(seat_id).colonies]
                  for seat_id in self.needs.seat_list()["joined"]}
        return tile_owners.problems(self.world.tile_owners, claims, self.world_map, ControlSnapshot(self.needs))
