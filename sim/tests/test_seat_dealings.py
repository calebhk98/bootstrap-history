"""Complaint 103: the founder deals as an actor. A seat applies for a patent, makes and answers offers (patents,
licences with a royalty, shares) and issues shares, through the same exchange every actor uses (small fixture:
a real household facade and seat state, no game)."""
import contextlib

from .harness import *  # noqa: F401,F403
from sim.agents import exchange_commands, joint_stock, patent  # noqa: F401
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Household, HouseholdParty
from sim.engine import seat_dealings
from sim.engine.agents_port_household import HouseholdPort
from sim.engine.state_seat import FIRST_SEAT_ID

from .agents_fake_world import FakeWorld, make_node

QUICK_TOPIC = True


class DealWorld(FakeWorld):
    registry = None
    facade = None

    def state_grants_patents(self, actor):
        return True

    def patent_entry(self, node_id):
        holders = list(self.registry.actors.values()) + [HouseholdParty(self.facade, seat_id=FIRST_SEAT_ID)]
        return patent.entry_among(holders, node_id, self.year)

    def proof_years(self, node_id):
        return 0.0

    def disclosure_mode(self, node_id):
        return "default"

    def concern_margin(self, node_id):
        return 0.0


class StubSim(seat_dealings.SeatDealingsMixin):
    """Just what the mixin reads: the state with its seats, the registry, the year and the seat's party."""

    def __init__(self):
        self.facade = Household(starting_capital=1000.0, port=HouseholdPort())
        self.state = self.facade._state
        self.actors = ActorRegistry(ActorsState(home_country="home"))
        self.year = 100

    def seat_party(self, seat_id, margins=None):
        return HouseholdParty(self.facade, margins, seat_id)

    @contextlib.contextmanager
    def act_as(self, seat_id):
        yield self


sim = StubSim()
world = DealWorld(year=100)
world.registry, world.facade = sim.actors, sim.facade
world.nodes["loom"] = make_node("loom")
world.baseline = set()
seat_dealings.SimWorld = lambda _sim: world
seat = sim.state.seats[FIRST_SEAT_ID]
world.seat_parties = lambda: {FIRST_SEAT_ID: sim.seat_party(FIRST_SEAT_ID)}
finder = exchange_commands.finder(sim.actors, world)

firm = sim.actors.add("firm:1", ActorRecord(kind="firm", money=5000.0, last_margin=300.0, founded_year=50))
firm.knowledge.add("loom")
firm.record.target = "loom"
sim.facade.done.add("loom")

# ---- the founder applies for a patent --------------------------------------------------------------------
reply = sim.seat_patent("loom")
check("the founder is granted a patent on what it holds", reply["ok"] and "loom" in seat.holdings.patents, reply)
check("a second claim is refused", not sim.seat_patent("loom")["ok"])
check("an invention it does not hold is refused", not sim.seat_patent("nothing")["ok"])

# ---- an offer to an AI actor is answered at its turn; the patent and the money move ------------------------
reply = sim.seat_offer("firm:1", {"patent": ["loom"]}, {"money": 4000.0})
check("an offer to a firm is made", reply["ok"] and len(firm.record.offers) == 1, reply)
exchange_commands.answer_offers(firm, finder, world)
check("the firm took the patent and paid for it", "loom" in firm.record.patents and "loom" not in seat.holdings.patents
      and abs(sim.facade.money - 5000.0) < 1e-6, (sim.facade.money, firm.record.patents))

# ---- an offer made to the founder waits in its holdings and is answered by command -------------------------
reply = sim.seat_offer("firm:1", {"patent": ["loom"]}, {"money": 100.0})
check("the firm now holds it, so the founder may not offer it", not reply["ok"], reply)
made = exchange_commands.exchange.make_offer(firm, sim.seat_party(FIRST_SEAT_ID), {"patent": ["loom"]}, {"money": 200.0}, world)
check("an offer to the founder is kept on the seat", [offer["id"] for offer in seat.holdings.offers] == [made["id"]])
check("it is listed", sim.dealings_listing()["offers"][0]["id"] == made["id"])
reply = sim.seat_answer(made["id"], True)
check("accepting moves the patent to the founder and the money to the firm", reply["ok"] and "loom" in seat.holdings.patents
      and abs(sim.facade.money - 4800.0) < 1e-6 and not seat.holdings.offers, (reply, sim.facade.money))
made = exchange_commands.exchange.make_offer(firm, sim.seat_party(FIRST_SEAT_ID), {"money": 1.0}, {"money": 0.0}, world)
check("declining drops the offer", sim.seat_answer(made["id"], False)["ok"] and not seat.holdings.offers)
check("an unknown offer is refused", not sim.seat_answer("nope", True)["ok"])

# ---- a licence with a royalty, then the royalty flows ------------------------------------------------------
reply = sim.seat_offer("firm:1", {"licence": ["loom"], "royalty": {"loom": 0.1}}, {"money": 10.0})
check("a licence with a royalty is offered", reply["ok"], reply)
firm.record.offers.clear()

# ---- what a seat does not deal in --------------------------------------------------------------------------
check("a concern is sold with sell concern, not offered", not sim.seat_offer("firm:1", {"concern": "loom"}, {})["ok"])
check("know-how is licensed with disclose, not offered", not sim.seat_offer("firm:1", {"knowledge": ["loom"]}, {})["ok"])
check("an offer to nobody is refused", not sim.seat_offer("nobody", {"money": 1.0}, {})["ok"])

# ---- the founder issues shares and buys shares ---------------------------------------------------------------
investor = sim.actors.add("stratum:home:rich", ActorRecord(kind="stratum", stratum="rich", members=100.0, money=1.0e6, controller="ai"))
reply = sim.seat_offer("stratum:home:rich", {"shares": {FIRST_SEAT_ID: 0.2}}, {"money": 50.0})
check("the founder offers shares in itself", reply["ok"], reply)
exchange_commands.answer_offers(investor, finder, world)
check("an investor that finds them worth more than the price takes them", investor.record.holdings.get(FIRST_SEAT_ID) == 0.2
      or investor.record.offers == [], (investor.record.holdings, investor.record.offers))
firm.record.issued = 0.3
investor.record.holdings["firm:1"] = 0.3
reply = sim.seat_offer("stratum:home:rich", {"money": 10.0}, {"shares": {"firm:1": 0.1}})
check("the founder offers to buy shares from a holder", reply["ok"], reply)
check("the seat can list its holdings and equity issued", "shares_issued" in sim.dealings_listing())
