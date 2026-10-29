"""Seats see each other as onlookers do: fog is each seat's own, another seat's work is heard of by what shows at
the distance, a secret does not spread, a licence moves a fee and the know-how, and the society counts every
seat's work (stand-ins and a household facade, no game)."""

QUICK_TOPIC = True

import contextlib
from types import SimpleNamespace

from .harness import check

from sim.agents import licence
from sim.agents.api import Household, HouseholdParty, OBSERVATION_RANGE_KM, PLAYER_VISIBLE_EXPOSURE, SECRET_EXPOSURE, ledger
from sim.ledger.api import PayActor
from sim.seats import api as seat_builds
from sim.knowledge.api import KnowledgeSeat
from sim.knowledge.rules import SeatTechniques, earliest_done_year as _earliest
from sim.actors.world import ActorWorld
from sim.engine.agents_port_household import HouseholdPort
from sim.tests.world_stand_in import fake_needs
from sim.engine.state import FounderState, HouseholdState, ProjectsState
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState, bind_seat
from sim.seats.api import SeatsSeat, base_visibility, most_open_mode, nodes_heard_of, seen_from
from sim.agents.api import Business


def earliest_done_year(seats, node_id, default):
    return _earliest([(seat.modules["knowledge"].done, seat.modules["knowledge"].done_year) for seat in seats.values()], node_id, default)


def techniques_of(seats):
    """What the knowledge module's `techniques_by_seat` view answers over these seats."""
    return {seat_id: SeatTechniques(frozenset(seat.modules["knowledge"].done), frozenset(seat.modules["knowledge"].granted))
            for seat_id, seat in seats.items()}


# ---- pure visibility
check("a published invention shows in full, a secret by its leak over its difficulty",
      base_visibility("publish", False, 4.0, 0.25) == 1.0 and base_visibility("secret", True, 4.0, 0.25) == 0.0625, None)
check("with no choice made, public use shows what the product gives away and privacy only what leaks",
      base_visibility("default", True, 3.0, 0.25) == 1.0 / 3.0 and base_visibility("default", False, 3.0, 0.25) == 0.25 / 3.0
      and base_visibility("default", True, 1.0, 0.25) == 1.0, None)
check("a technique whose product gives it away shows in full when run in public, one that hides it does not",
      base_visibility("default", True, 1.0 / 0.9, 0.25) > base_visibility("default", True, 1.0 / 0.15, 0.25), None)
check("distance thins what shows", seen_from(1.0, 0.0, 800.0) == 1.0 and seen_from(1.0, 800.0, 800.0) == 0.5, None)
check("one maker publishing opens an invention for everyone", most_open_mode(["secret", "publish", "license"]) == "publish"
      and most_open_mode(["secret", "license"]) == "license" and most_open_mode([]) == "default", None)

# ---- two seats with their own knowledge
state_facade = Household(starting_capital=100.0, port=HouseholdPort(),
                         techniques_held=lambda: frozenset(state.seats[state.acting_seat].modules["knowledge"].done))
state = state_facade._state
first, second = state.seats[FIRST_SEAT_ID], SeatState(
    household=HouseholdState(capital=40.0), projects=ProjectsState(), founder=FounderState(),
    modules={"knowledge": KnowledgeSeat(granted={"base"}, done={"base"})})
state.seats["second"] = second
first.modules["knowledge"] = KnowledgeSeat()
first_knowledge, second_knowledge = first.modules["knowledge"], second.modules["knowledge"]
first_knowledge.done.update({"base", "lathe", "loom"})
first_knowledge.granted.add("base")
first_knowledge.done_year = {"lathe": 120, "loom": 130}
second_knowledge.done.add("kiln")
seats = state.seats
disclosed = {FIRST_SEAT_ID: {}, "second": {}}   # what each seat chose for its inventions (the diffusion module keeps it)

check("what a seat built excludes what its country already had",
      seat_builds.builders_of(techniques_of(seats), "lathe") == [FIRST_SEAT_ID] and seat_builds.builders_of(techniques_of(seats), "base") == []
      and seat_builds.builders_of(techniques_of(seats), "kiln") == ["second"], None)
check("the society counts every seat's work, a node built by the second seat alone included",
      seat_builds.built_by_any(techniques_of(seats)) == {"lathe", "loom", "kiln"}, None)
check("the society copies from whichever seat finished it first",
      earliest_done_year(seats, "lathe", 200) == 120 and earliest_done_year(seats, "kiln", 200) == 200, None)
second_knowledge.done.add("lathe")
second_knowledge.done_year = {"lathe": 110}
check("a node both built is as old as the earlier maker's", earliest_done_year(seats, "lathe", 200) == 110, None)
second_knowledge.done.discard("lathe")
check("what one seat has revealed is not what another has", first_knowledge.revealed is not second_knowledge.revealed, None)

# ---- hearing of another seat's work, as an onlooker does
def built_by_first():
    return first_knowledge.done - first_knowledge.granted


def known_to_second():
    return second_knowledge.done | second_knowledge.revealed


first_operating = {"loom"}   # what the first seat runs (the ventures module keeps it)
disclosed[FIRST_SEAT_ID]["lathe"] = {"mode": "secret", "published_year": None, "licensees": {}}
heard_near = nodes_heard_of(built_by_first(), first_operating, disclosed[FIRST_SEAT_ID], known_to_second(), 0.0, lambda node_id: 1.0)
check("a concern run in public is heard of from beside it, a secret is not",
      heard_near == {"loom"}, heard_near)
heard_far = nodes_heard_of(built_by_first(), first_operating, disclosed[FIRST_SEAT_ID], known_to_second(), 10 * OBSERVATION_RANGE_KM, lambda node_id: 1.0)
check("distance hides it", heard_far == set(), heard_far)
disclosed[FIRST_SEAT_ID]["lathe"] = {"mode": "publish", "published_year": 125, "licensees": {}}
check("a published invention is heard of from a fair way off",
      "lathe" in nodes_heard_of(built_by_first(), first_operating, disclosed[FIRST_SEAT_ID], known_to_second(), OBSERVATION_RANGE_KM * 0.5, lambda node_id: 1.0), None)
second_knowledge.revealed.add("loom")
check("what a seat has already heard of is not heard again",
      "loom" not in nodes_heard_of(built_by_first(), first_operating, disclosed[FIRST_SEAT_ID], known_to_second(), 0.0, lambda node_id: 1.0), None)
check("a secret leaks less than the visibility that makes an invention heard of",
      SECRET_EXPOSURE < PLAYER_VISIBLE_EXPOSURE, (SECRET_EXPOSURE, PLAYER_VISIBLE_EXPOSURE))


# ---- the actors' view of the world counts every seat
class Places:
    """Where each seat works from, so distances are decided here."""
    first, second = "near", "far"


class StubModule:
    """The actors module over the seats of this test: the views the world reads."""

    def __init__(self):
        self.cast = lambda: SimpleNamespace(actors={})
        self.needs = fake_needs(
            legacy_seats=state.seats, operating_by_seat=lambda: {FIRST_SEAT_ID: first_operating, "second": set()}, techniques_granted=lambda: first_knowledge.granted, techniques_by_seat=lambda: techniques_of(state.seats), tree_nodes={}, acting_seat=lambda: state.acting_seat, disclosures=disclosed,
            copy_difficulty=lambda node_id: 1.0, seat_place=lambda seat_id: Places.first if seat_id == FIRST_SEAT_ID else Places.second,
            disclosure=lambda node_id: {"mode": "default", "licensees": {}})


class World(ActorWorld):
    def distance_km(self, place_a, place_b):
        return 0.0 if place_a == place_b else OBSERVATION_RANGE_KM


world = World(StubModule())
check("the actors see the inventions of every seat", world.founder_inventions() == ["kiln", "lathe", "loom"], world.founder_inventions())
check("a concern some seat runs is in public use", world.is_public("loom") and not world.is_public("kiln"), None)
disclosed[FIRST_SEAT_ID]["lathe"] = {"mode": "secret", "published_year": None, "licensees": {}}
check("an observer at the maker's door sees a secret less than a published work",
      world.exposure("lathe", Places.first) < world.exposure("loom", Places.first), None)
check("an observer a range away from the maker sees half what one at the door does",
      abs(world.exposure("loom", Places.second) - world.exposure("loom", Places.first) / 2.0) < 1e-9, None)
second_knowledge.done.add("lathe")
disclosed["second"]["lathe"] = {"mode": "publish", "published_year": 130, "licensees": {}}
check("a second maker publishing the same invention makes it public knowledge",
      world.disclosure_mode("lathe") == "publish", world.disclosure_mode("lathe"))
second_knowledge.done.discard("lathe")
del disclosed["second"]["lathe"]
check("the best view of an invention is from the nearest maker's place",
      world.exposure("kiln", Places.second) >= world.exposure("kiln", Places.first), None)


# ---- a licence between seats moves a fee and the know-how, and the know-how is not the licensee's own work
def act_as(seat_id):
    @contextlib.contextmanager
    def switch():
        previous = state.acting_seat
        bind_seat(state, seat_id)
        try:
            yield
        finally:
            bind_seat(state, previous)
    return switch()


def receive(nodes, granted):
    """What the engine's `ReceiveTechniques` does for the seat that is acting."""
    knowledge = state.seats[state.acting_seat].modules["knowledge"]
    knowledge.done.update(nodes)
    if granted:
        knowledge.granted.update(nodes)


maker = HouseholdParty(state_facade, seat_id=FIRST_SEAT_ID, act_as=act_as, dealings=SeatsSeat(), receive=receive, business=Business())
buyer = HouseholdParty(state_facade, seat_id="second", act_as=act_as, dealings=SeatsSeat(), receive=receive, business=Business())


class LicenceWorld:
    nodes = {"lathe": {"pre": []}}

    def patent_entry(self, node_id):
        return None

    def demonstrated(self):
        return {"lathe"}

    def baseline_knowledge(self):
        return {"base"}


maker_before, buyer_before = maker.money, buyer.money
terms = licence.terms_problem(buyer, 10.0, 0.0)
royalty_terms = licence.terms_problem(buyer, 10.0, 0.1)
check("a seat can be licensed for a fee and not for a royalty, which is a share of a firm's takings",
      terms == "" and royalty_terms != "", (terms, royalty_terms))
granted = licence.grant(maker, buyer, "lathe", 10.0, LicenceWorld())
check("the fee moves from the licensee seat to the licensor seat",
      granted and abs(maker.money - maker_before - 10.0) < 1e-9 and abs(buyer.money - buyer_before + 10.0) < 1e-9, (maker.money, buyer.money))
check("the licensee seat now holds the know-how", "lathe" in second_knowledge.done, None)
check("a licensed-in node is held as received, not built, so it adds no maker and opens nothing",
      "lathe" in second_knowledge.granted and seat_builds.builders_of(techniques_of(seats), "lathe") == [FIRST_SEAT_ID], None)
check("it cannot be licensed twice to the same seat", licence.grant(maker, buyer, "lathe", 10.0, LicenceWorld()) is False, None)


# ---- a licensed firm's royalty reaches the seat that licensed it
class Firm:
    actor_id = "firm:7"

    def __init__(self):
        self.money = 100.0

    def debit(self, amount, purpose):
        self.money -= amount

    def credit(self, amount, purpose):
        self.money += amount


class RoyaltySim:
    """The actors module over the seats of this test: the views the royalty reads."""

    def __init__(self):
        self.cast = lambda: SimpleNamespace(actors={}, patent_holders=lambda node_id: [], get=lambda actor_id: None)
        parties = lambda seat_id: maker if seat_id == FIRST_SEAT_ID else buyer
        self.needs = fake_needs({PayActor: lambda command: ledger.transfer(firm, parties(command.payee), command.amount, command.purpose)},
                                legacy_seats=state.seats, techniques_by_seat=lambda: techniques_of(state.seats), disclosures=disclosed, seat_party=parties)


disclosed[FIRST_SEAT_ID]["lathe"] = {"mode": "license", "published_year": None,
                                       "licensees": {"firm:7": {"fee": 0.0, "royalty": 0.1, "year": 120}}}
firm = Firm()
royalty_world = World(RoyaltySim())
before = maker.money
paid = royalty_world.collect_royalty(firm, "lathe", 200.0)
check("the royalty goes to the seat that licensed the invention and to nobody else",
      abs(paid - 20.0) < 1e-9 and abs(maker.money - before - 20.0) < 1e-9 and abs(firm.money - 80.0) < 1e-9, (paid, maker.money, firm.money))
check("a firm nobody licensed owes nobody", royalty_world.collect_royalty(Firm(), "loom", 200.0) == 0.0, None)
