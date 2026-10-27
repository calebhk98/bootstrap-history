"""Effect operations: the supported way for mod code, and the base game's own systems, to change the world.

Each operation goes through the normal rules: money moves through the ledger against a named edge, goods through the
economy's book against a named edge (so the conservation checks see them), people through the population and strata,
a tile through `transfer_tile`, a store through `sim.stores.write`. Every operation that changes the world needs a
cause and writes it to the world event log (the hazards module). A mod reaches these as `api.effects`; its
kinds and edge names are forced into its `<mod_id>:` namespace. The base game uses `BASE_EFFECTS`."""
from typing import Any, Iterable, Optional

from sim.agents.api import edges as edge_names
from . import economy_port_effects as economy_api

from sim.demography.api import KillPeople
from sim.hazards.api import RecordWorldEvent
from sim.land.api import TransferTile
from sim.ledger.api import PayActor, PayActorFromEdge, PayEdgeFrom
from sim.stores.api import WriteStore

from .mods_base import ModError
from .mods_ids import SEPARATOR

KNOWN_EDGES = frozenset(value for name, value in vars(edge_names).items() if name.startswith("EDGE_") and isinstance(value, str)) \
    | {economy_api.EDGE_PRODUCTION, economy_api.EDGE_CONSUMPTION, economy_api.EDGE_WEAR, economy_api.EDGE_EXTERNAL}
EDGE_PREFIX = "edge:"


class ModEffects:
    """What `api.effects` returns. `owner` is the mod id, or empty for the base game."""

    def __init__(self, owner: str = ""):
        self.owner = owner

    # ---- names ------------------------------------------------------------------------------------------

    def kind(self, kind: str) -> str:
        return kind if not self.owner or kind.startswith(self.owner + SEPARATOR) else self.owner + SEPARATOR + kind

    def edge_name(self, edge: Optional[str]) -> str:
        """A named edge: one the book declares, or one namespaced to this mod (`edge:<mod_id>:<name>`)."""
        own = self.owner and isinstance(edge, str) and edge.startswith(EDGE_PREFIX + self.owner + SEPARATOR)
        if edge not in KNOWN_EDGES and not own:
            raise ModError("%s needs a named edge (one of the declared edges, or edge:%s:<name>), not %r"
                           % (self.label(), self.owner or "<name>", edge))
        return edge

    def label(self) -> str:
        return "mod %s" % self.owner if self.owner else "the base game"

    def need_cause(self, cause: Any) -> str:
        if not isinstance(cause, str) or not cause.strip():
            raise ModError("%s: a change to the world needs a cause in words" % self.label())
        return cause

    # ---- money ------------------------------------------------------------------------------------------

    def pay(self, sim: Any, payer_id: str, payee_id: str, amount: float, purpose: str) -> None:
        """Move coin between two actors through the ledger."""
        self._actor(sim, payer_id), self._actor(sim, payee_id)
        sim.send(PayActor(payer_id, payee_id, self._amount(amount), self.need_cause(purpose)))

    def pay_edge(self, sim: Any, actor_id: str, edge: str, amount: float, purpose: str) -> None:
        """An actor pays a named edge: the coin leaves every purse and the edge keeps what crossed it."""
        self._actor(sim, actor_id)
        sim.send(PayEdgeFrom(actor_id, self.edge_name(edge), self._amount(amount), self.need_cause(purpose)))

    def receive_from_edge(self, sim: Any, actor_id: str, edge: str, amount: float, purpose: str) -> None:
        """A named edge pays an actor: coin enters the purses, and the edge's book shows where it came from."""
        self._actor(sim, actor_id)
        sim.send(PayActorFromEdge(self.edge_name(edge), actor_id, self._amount(amount), self.need_cause(purpose)))

    # ---- goods ------------------------------------------------------------------------------------------

    def add_goods(self, sim: Any, account_id: str, good: str, tile: str, quantity: float, cause: str,
                  edge: str = economy_api.EDGE_PRODUCTION) -> None:
        """Goods come into the world at a tile, into an account of the economy's book, from a named edge."""
        move = economy_api.GoodsMove(self.edge_name(edge), account_id, good, tile, self._amount(quantity), self._goods_purpose(cause))
        economy_api.move_goods(self._economy(sim), [move])

    def remove_goods(self, sim: Any, account_id: str, good: str, tile: str, quantity: float, cause: str,
                     edge: str = economy_api.EDGE_CONSUMPTION) -> None:
        """Goods leave the world from an account at a tile, to a named edge; more than the account holds is refused."""
        move = economy_api.GoodsMove(account_id, self.edge_name(edge), good, tile, self._amount(quantity), self._goods_purpose(cause))
        economy_api.move_goods(self._economy(sim), [move])

    # ---- people -----------------------------------------------------------------------------------------

    def kill_people(self, sim: Any, country: str, share: float, cause: str, kind: str = "deaths",
                    tiles: Iterable[str] = (), **facts: Any) -> dict:
        """Remove `share` of a country's people (the home society by its age cohorts, a partner by its strata); writes
        the event, whose facts carry `died`, and returns it."""
        cause = self.need_cause(cause)
        if not 0.0 <= share <= 1.0:
            raise ModError("%s: a death share is between 0 and 1, not %r" % (self.label(), share))
        return sim.send(KillPeople(country, share, cause, kind=self.kind(kind), tiles=tuple(tiles), facts=dict(facts)))

    def move_people(self, sim: Any, from_stratum_id: str, to_stratum_id: str, count: float, cause: str) -> dict:
        """Move people between two strata (migration, or reassignment to another class); the total stays the same."""
        cause = self.need_cause(cause)
        source, target = self._stratum(sim, from_stratum_id), self._stratum(sim, to_stratum_id)
        moved = min(self._amount(count), source.record.members)
        source.record.members -= moved
        target.record.members += moved
        countries = [source.record.country or sim.civ["id"], target.record.country or sim.civ["id"]]
        return sim.send(RecordWorldEvent(self.kind("people_moved"), actors=tuple(sorted(set(countries))), cause=cause,
                                         facts=dict(moved=moved, from_stratum=from_stratum_id, to_stratum=to_stratum_id)))

    # ---- tiles, stores, events ----------------------------------------------------------------------------

    def transfer_tile(self, sim: Any, tile_id: str, to_actor: Optional[str], cause: str, control: Optional[str] = None) -> Optional[str]:
        """Give a tile to a country or seat (None releases it); the world event log records it with the cause."""
        return sim.send(TransferTile(tile_id, to_actor, self.need_cause(cause), control))

    def write_store(self, sim: Any, name: str, key: Any, value: Any) -> None:
        """Write one value of a store this owner declared; another owner's store is an error."""
        sim.send(WriteStore(name, key, value, self.owner))

    def record_event(self, sim: Any, kind: str, cause: str, actors: Iterable[str] = (), tiles: Iterable[str] = (), **facts: Any) -> dict:
        """Write a record to the world event log."""
        return sim.send(RecordWorldEvent(self.kind(kind), actors=tuple(actors), tiles=tuple(tiles), cause=self.need_cause(cause),
                                         facts=dict(facts)))

    # ---- helpers ------------------------------------------------------------------------------------------

    def _amount(self, amount: Any) -> float:
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not amount >= 0.0:
            raise ModError("%s: an amount is a number of zero or more, not %r" % (self.label(), amount))
        return float(amount)

    def _goods_purpose(self, cause: str) -> str:
        return "%s: %s" % (self.label(), self.need_cause(cause))

    def _actor(self, sim: Any, actor_id: str) -> Any:
        actor = sim.view("cast")().get(actor_id)
        if actor is None:
            raise ModError("%s: no actor %r" % (self.label(), actor_id))
        return actor

    def _stratum(self, sim: Any, stratum_id: str) -> Any:
        actor = self._actor(sim, stratum_id)
        if actor.record.kind != "stratum":
            raise ModError("%s: %r is not a stratum" % (self.label(), stratum_id))
        return actor

    @staticmethod
    def _economy(sim: Any) -> Any:
        return sim.view("legacy_economy")().agent.economy()


def strata_of(sim: Any, country: str) -> list:
    return [actor for actor in sim.view("cast")().of_kind("stratum") if (actor.record.country or sim.civ["id"]) == country]


def people_of(sim: Any, country: str) -> float:
    """How many people the country holds: the home society's population, or a partner's strata."""
    if country == sim.civ["id"]:
        return float(sim.view("population")().total)
    return sum(actor.record.members for actor in strata_of(sim, country))


BASE_EFFECTS = ModEffects("")
