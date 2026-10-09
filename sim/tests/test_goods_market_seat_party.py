"""The goods market names the acting seat as its party: two seats do not collide in the year's flows, the posted price
leaves out only the asking seat's orders (small fixture, no game)."""
from .harness import *  # noqa: F401,F403
from sim.engine.agents_port_household import HouseholdPort
from sim.engine.goods_market_api import GoodsMarket
from sim.engine.market_clearing import MarketClearingMixin
from sim.engine.state import FounderState, HouseholdState, ProjectsState
from sim.engine.state_seat import FIRST_SEAT_ID, SeatState, bind_seat

QUICK_TOPIC = True


class FixtureSim(MarketClearingMixin):
    """The state and the seat switch; the market code reads nothing else for flows."""

    def __init__(self):
        self.state = HouseholdPort().fresh_state(100.0)
        self.state.seats["second"] = SeatState(household=HouseholdState(capital=5.0), projects=ProjectsState(),
                                               founder=FounderState())

    def act_as(self, seat_id):
        sim = self

        class Switch:
            def __enter__(self_inner):
                self_inner.previous = sim.state.acting_seat
                bind_seat(sim.state, seat_id)

            def __exit__(self_inner, *exc):
                bind_seat(sim.state, self_inner.previous)
        return Switch()


sim = FixtureSim()
market = GoodsMarket(sim)
first, second = FIRST_SEAT_ID, "second"
check("the acting party is the acting seat's id", market.acting_party_id == first and market.acting.party_id == first, None)
check("a party for each seat, the same object each time",
      market.seat_party(second) is market.seat_party(second) and market.seat_party(second).party_id == second, None)

market.note_sale(first, "iron", 3.0)
market.note_sale(second, "iron", 5.0)
market.note_sale("firm:1", "iron", 7.0)
check("two seats' sales are separate entries in one commodity",
      market.sold_tonnes("iron", first) == 3.0 and market.sold_tonnes("iron", second) == 5.0, None)
check("the asking seat's sales are left out of the others, the other seat's are not",
      market.others_sold_tonnes("iron") == 12.0, market.others_sold_tonnes("iron"))
bind_seat(sim.state, second)
check("with the second seat asking, the first seat counts among the others",
      market.acting_party_id == second and market.others_sold_tonnes("iron") == 10.0, market.others_sold_tonnes("iron"))
bind_seat(sim.state, first)

market.note_purchase(second, "iron", 2.0)
stamp = market.others_stamp()
bind_seat(sim.state, second)
check("the stamp for caches leaves out the asking seat only", stamp != market.others_stamp(), None)
bind_seat(sim.state, first)

sim.state.scenario.year += 1
sim._market_flows()
check("a new year clears every seat's flows and keeps the firm's standing sale",
      market.sold_tonnes("iron", first) == 0.0 and market.sold_tonnes("iron", second) == 0.0
      and market.sold_tonnes("iron", "firm:1") == 7.0, None)
