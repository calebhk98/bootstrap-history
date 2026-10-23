"""Armies in the game: where they are kept, who owns them, and what raising, ordering, recalling and disbanding one is.

The armies of every actor are records in `state.economy.campaigns["armies"]` ({army id: Army as a dict}); the
rules that move and fight them are in `sim/world/campaign_*.py` and `battle.py`, the year's phase in
`campaign_year.py`. An owner is any actor that owns tiles; its soldiers are the force its government keeps (the
army line), an army being a slice of them. A seat that plays a country raises armies for that country."""
from typing import Any, Dict, List, Optional

from sim.agents.api import army_raising
from sim.geography.api import settlement
from sim.refusal import Refusal
from sim.world import campaign_supply
from sim.world.army_record import Army, fielded_soldiers


class CampaignActorsMixin:

    def campaign_store(self) -> Dict[str, Any]:
        store = self.state.economy.campaigns
        store.setdefault("armies", {})
        store.setdefault("drawn", {})        # tile -> food energy armies have taken from it this year
        store.setdefault("held_since", {})   # tile -> {year, by, from} for tiles taken by an army
        store.setdefault("next_id", 1)
        return store

    def army_records(self) -> Dict[str, Dict[str, Any]]:
        return self.campaign_store()["armies"]

    def army_of(self, army_id: str) -> Optional[Army]:
        record = self.army_records().get(army_id)
        return None if record is None else Army.from_dict(record)

    def armies_of(self, owner: str) -> List[Army]:
        return [Army.from_dict(record) for _, record in sorted(self.army_records().items()) if record["owner"] == owner]

    def acting_owner(self) -> str:
        """The actor the acting seat raises armies for: the country it plays, else the game's own."""
        seat = self.state.seats[self.state.acting_seat]
        return seat.country or str(self.civ["id"])

    def owner_has_state(self, owner: str) -> bool:
        """Whether the owner is a country with a state (a seat's colony or a bare owner has no soldiers to raise)."""
        return owner == str(self.civ["id"]) or owner in self.actors.state.countries

    def owner_world(self, owner: str) -> Any:
        """The world the owner's state sees (the shared one for the home country, else its country's scope)."""
        from .agents_port import SimWorld
        return self.actors.world_of_country(owner, SimWorld(self))

    def owner_government(self, owner: str) -> Any:
        return self.owner_world(owner).government()

    def owner_force(self, owner: str) -> float:
        """Soldiers the owner's state keeps now."""
        return float(self.owner_world(owner).soldiers_under_arms()) if self.owner_has_state(owner) else 0.0

    def free_soldiers(self, owner: str) -> float:
        return army_raising.available_soldiers(self.owner_force(owner), fielded_soldiers(self.army_records(), owner))

    def strike_from_force(self, owner: str, killed: float) -> None:
        """Take soldiers who died in the field off the owner's army line."""
        if killed <= 0.0 or not self.owner_has_state(owner):
            return
        record = self.owner_government(owner).record
        record.army = army_raising.struck_from_force(self.owner_force(owner), killed)

    def save_army(self, army: Army) -> None:
        self.army_records()[army.army_id] = army.to_dict()

    def raise_army(self, owner: str, soldiers: Any, tile: Optional[str] = None) -> Any:
        """Raise an army of `soldiers` of the owner's force on one of its tiles (the best-endowed one when none is named);
        the new `Army`, or a Refusal."""
        owned = self.tiles_owned_by(owner)
        tile = tile or (settlement.default_base_tile(owned) if owned else None)
        refusal = army_raising.raise_refusal(soldiers, self.free_soldiers(owner), self.tile_owner(tile) if tile else None,
                                             owner, tile in self.world_map.tiles if tile else False)
        if refusal is not None:
            return refusal
        store = self.campaign_store()
        army_id = "army_%d" % store["next_id"]
        store["next_id"] += 1
        world = self.owner_world(owner)
        army = Army(army_id, owner, tile, float(soldiers), float(world.equipment_kg_per_soldier()),
                    animals=float(soldiers) * campaign_supply.TRAIN_ANIMALS_PER_SOLDIER, home_tile=tile,
                    raised_year=int(self.state.scenario.year))
        self.save_army(army)
        return army

    def own_army(self, owner: str, army_id: Any) -> Any:
        """The owner's army of this id, or a Refusal."""
        record = self.army_records().get(army_id)
        if record is None:
            return Refusal("unknown_army", "no army %r. Nothing was changed." % (army_id,),
                           sorted(key for key, other in self.army_records().items() if other["owner"] == owner))
        if record["owner"] != owner:
            return Refusal("not_your_army", "army %s is not yours. Nothing was changed." % army_id)
        return Army.from_dict(record)

    def order_army(self, owner: str, army_id: Any, tile: Any) -> Any:
        """Send an army to a tile; it marches from the next year's campaign (or this year's, if the year has not run)."""
        army = self.own_army(owner, army_id)
        if isinstance(army, Refusal):
            return army
        if not isinstance(tile, str) or tile not in self.world_map.tiles:
            return Refusal("unknown_tile", "no such tile on the map. Nothing was changed.")
        army.target, army.progress_days = (None if tile == army.tile else tile), 0.0
        self.save_army(army)
        return army

    def recall_army(self, owner: str, army_id: Any) -> Any:
        """Order an army back to the tile it was raised on, or to the owner's best-endowed tile if that is no longer
        the owner's."""
        army = self.own_army(owner, army_id)
        if isinstance(army, Refusal):
            return army
        home = army.home_tile if self.tile_owner(army.home_tile) == owner else None
        owned = self.tiles_owned_by(owner)
        home = home or (settlement.default_base_tile(owned) if owned else None)
        if home is None:
            return Refusal("no_tile_to_return_to", "the owner holds no tile to recall the army to. Nothing was changed.")
        return self.order_army(owner, army_id, home)

    def disband_army(self, owner: str, army_id: Any) -> Any:
        """Stand an army down: its soldiers go back to the state's force, its food and animals are dispersed."""
        army = self.own_army(owner, army_id)
        if isinstance(army, Refusal):
            return army
        del self.army_records()[army_id]
        return army
