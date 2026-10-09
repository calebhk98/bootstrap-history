"""The civilisation's loanable-funds market, as the simulation keeps it.

Once a year, before the actors act, the market meets: what households, firms, the founder and the
state hold is the supply of funds; what the founder, firms and the state owe, and what the economy
the simulation does not model actor by actor borrows, is the demand. The rate follows the balance
(`sim/world/capital_market.py`), and the funds lenders will still advance are what every borrower's
credit limit is bounded by (`economy_credit.py`, `actors/borrowing.py`).
"""
from sim.agents.api import EDGE_SAVERS
from sim.constants import declare
from sim.world import capital_market


LENDING_HORIZON_YEARS = declare(
    "LENDING_HORIZON_YEARS", 10.0, kind="temporary_heuristic",
    unit="years of household saving", source=None, confidence="D",
    why="How many years of what households save stand as funds lenders hold in loanable form. Stands "
        "in for an accumulating stock of savings with its own losses and uses.")
BACKGROUND_BORROWING_SHARE = declare(
    "BACKGROUND_BORROWING_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of the funds households' saving supports", source=None, confidence="D",
    why="What the economy the simulation does not model actor by actor (farmers, traders, landlords) "
        "borrows against the same savings. Stands in for those borrowers.")
LENDABLE_RESERVE_SHARE = declare(
    "LENDABLE_RESERVE_SHARE", 0.1, kind="temporary_heuristic",
    unit="share of the state's reserve beyond a year's need", source=None, confidence="D",
    why="How much of its spare reserve a state puts into the loanable pool (the rest stays as coin and "
        "bullion). Stands in for a treasury's investment policy.")

SEAT_SOURCE_PREFIX = "seat:"   # a seat's own savings among the funds lenders hold


class CapitalMarketMixin:

    def _market_record(self):
        state = self.state.actors
        return None if state is None else state.markets.get(str(self.civ.get("id")))

    def capital_market(self):
        """The civilisation's market record, created empty before its first meeting."""
        from .state import CapitalMarketRecord
        markets = self.actors.state.markets
        civ_id = str(self.civ.get("id"))
        if civ_id not in markets:
            markets[civ_id] = CapitalMarketRecord()
        return markets[civ_id]

    def market_rate(self):
        """The yearly market rate: the civilisation's starting rate until the market has met; on the
        agent economy, its credit market's rate."""
        rate = self.economy.agent_rate()
        if rate is not None:
            return capital_market.bounded_rate(float(self.civ["starting_interest_rate"]), rate)
        record = self._market_record()
        if record is None or record.supply <= 0.0:
            return float(self.civ["starting_interest_rate"])
        return record.rate

    def market_credit_room(self, actor_id):
        """What lenders will advance one borrower beyond what the others owe; None before they have met. On
        the agent economy, its credit market answers, as it does for the rate."""
        answered, room = self.economy.agent_credit_room(actor_id)
        if answered:
            return room
        record = self._market_record()
        if record is None or record.supply <= 0.0:
            return None
        others = sum(owed for borrower, owed in record.loans.items() if borrower != actor_id)
        return capital_market.headroom(record.capacity, others)

    def market_loans(self):
        """Everything modelled borrowers owe, by borrower."""
        loans = {seat_id: max(0.0, -seat.household.capital) for seat_id, seat in self.state.seats.items()}
        for actor_id in sorted(self.actors.actors):
            actor = self.actors.actors[actor_id]
            if actor.record.exited_year is not None:
                continue
            loans[actor_id] = actor.debt()
        loans[self.MERCHANTS_BORROWER] = self.merchant_borrowing()
        return loans

    def market_funds(self, world):
        """Funds lenders hold, by source."""
        gov = self.state_treasury()
        firms = sum(max(0.0, firm.money) for firm in self.actors.active_firms())
        spare = max(0.0, gov.money - sum(gov.record.need.values()))
        funds = {
            "households": LENDING_HORIZON_YEARS * world.household_saving(),
            "firms": firms,
            "state": LENDABLE_RESERVE_SHARE * spare,
        }
        for seat_id, seat in self.state.seats.items():
            funds[SEAT_SOURCE_PREFIX + seat_id] = max(0.0, seat.household.capital)
        return funds

    def state_lending(self):
        """(what the state has out on loan, the yearly rate lenders earn): the claims the state holds in the
        actors' book, and the market rate."""
        return self.actors.state.purses.lent(self.state_treasury().actor_id), self.market_rate()

    def lender_offers(self, sources):
        """The funds each lender account offers this year, from the market's sources: the households' savings
        stand behind the savers, the state's reserve behind its account, a seat's savings behind the seat's, and
        each firm's purse behind the firm's."""
        offers = {EDGE_SAVERS: sources["households"], self.state_treasury().actor_id: sources["state"]}
        for seat_id in self.state.seats:
            offers[seat_id] = sources[SEAT_SOURCE_PREFIX + seat_id]
        purses = self.actors.state.purses
        for firm in self.actors.active_firms():
            offers[firm.actor_id] = purses.purse(firm.actor_id)
        return offers

    def update_capital_market(self):
        """The year's meeting: set the rate from the balance and record what lenders will advance."""
        from .agents_port import SimWorld
        world = SimWorld(self)
        record = self.capital_market()
        sources = self.market_funds(world)
        self.actors.state.purses.set_offers(self.lender_offers(sources))
        supply = sum(sources.values())
        loans = self.market_loans()
        background = BACKGROUND_BORROWING_SHARE * sources["households"]
        current = capital_market.utilisation(background + sum(loans.values()), supply)
        starting = float(self.civ["starting_interest_rate"])
        if record.reference_utilisation <= 0.0 and 0.0 < current < float("inf"):
            record.reference_utilisation = current
        record.rate = capital_market.rate_for_balance(starting, current, record.reference_utilisation)
        record.supply_by_source = sources
        record.supply = supply
        record.background = background
        record.capacity = max(0.0, capital_market.lendable_capacity(supply) - background)
        record.loans = loans
        return record

    def capital_market_report(self):
        """The market as a player sees it: the rate, what lenders hold and will still advance the founder,
        and what the state owes."""
        record = self._market_record()
        gov = "government:" + str(self.civ.get("id"))
        if record is None or record.supply <= 0.0:
            return {"market_rate": round(self.market_rate(), 4), "met": False}
        room = self.market_credit_room(self.state.acting_seat)
        return {
            "met": True,
            "market_rate": round(record.rate, 4),
            "funds_lenders_hold": round(record.supply, 1),
            "lenders_will_still_advance_you": None if room is None else round(room, 1),
            "the_state_owes": round(record.loans.get(gov, 0.0), 1),
            "the_state_has_lent": round(self.state_lending()[0], 1),
            "means": "the yearly rate on loans in your civilisation, set by the funds its households, "
                     "firms and state save against what everyone borrows; your own rate is this plus "
                     "a premium for how much of your limit you use, less your standing",
        }
