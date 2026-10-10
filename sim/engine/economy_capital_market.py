"""The funds lenders offer the engine's borrowers, read from the agent economy and the actors' book.

The rate and the room a borrower may still be lent are the agent economy's credit market's. What the engine adds
is who lends to its own actors: once a year, before the actors act, the lenders' offers are fixed from what
households save, what the state holds beyond its need and what each firm holds, and the actors' draws on
their facilities are shared among them (`sim/agents/purses.py`). What the founder, firms and the state owe is the
claims in that book.
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


class CapitalMarketMixin:

    def market_rate(self):
        """The yearly market rate: the agent economy's credit market's, or the civilisation's starting rate while
        the economy opens."""
        rate = self.economy.agent_rate()
        if rate is not None:
            return capital_market.bounded_rate(float(self.civ["starting_interest_rate"]), rate)
        return float(self.civ["starting_interest_rate"])

    def market_credit_room(self, actor_id):
        """What lenders will advance one borrower beyond what the others owe; None before they have met (the
        agent economy's credit market answers)."""
        answered, room = self.economy.agent_credit_room(actor_id)
        return room if answered else None

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
        return funds

    def state_lending(self):
        """(what the state has out on loan, the yearly rate lenders earn): the claims the state holds in the
        actors' book, and the market rate."""
        return self.actors.state.purses.lent(self.state_treasury().actor_id), self.market_rate()

    def lender_offers(self, sources):
        """The funds each lender account offers this year, from the market's sources: the households' savings
        stand behind the savers, the state's reserve behind its account and each firm's purse behind the firm's. A
        player's seat is not a lender: its purse is its own."""
        offers = {EDGE_SAVERS: sources["households"], self.state_treasury().actor_id: sources["state"]}
        purses = self.actors.state.purses
        for firm in self.actors.active_firms():
            offers[firm.actor_id] = purses.purse(firm.actor_id)
        return offers

    def refresh_lender_offers(self):
        """The year's meeting of lenders: fix who offers what to the actors' borrowers."""
        from .agents_port import SimWorld
        self.actors.state.purses.set_offers(self.lender_offers(self.market_funds(SimWorld(self))))

    def lent_share(self):
        """Share of lenders' funds out on loan: what the actors owe and the economy the simulation does not model
        actor by actor borrows (a share of the households' savings), over the funds on offer."""
        purses = self.actors.state.purses
        supply = sum(purses.offers.values())
        if supply <= 0.0:
            return 0.0
        background = BACKGROUND_BORROWING_SHARE * purses.offers.get(EDGE_SAVERS, 0.0)
        demanded = capital_market.utilisation(background + purses.lent(), supply)
        return min(1.0 - capital_market.LENDER_RESERVE_SHARE, demanded)

    def capital_market_report(self):
        """The market as a player sees it: the rate, what lenders hold and will still advance the founder,
        and what the state owes."""
        purses = self.actors.state.purses
        supply = sum(purses.offers.values())
        if supply <= 0.0:
            return {"market_rate": round(self.market_rate(), 4), "met": False}
        room = self.market_credit_room(self.state.acting_seat)
        return {
            "met": True,
            "market_rate": round(self.market_rate(), 4),
            "funds_lenders_hold": round(supply, 1),
            "lenders_will_still_advance_you": None if room is None else round(room, 1),
            "the_state_owes": round(purses.debt(self.state_treasury().actor_id), 1),
            "the_state_has_lent": round(self.state_lending()[0], 1),
            "means": "the yearly rate on loans in your civilisation, set by the funds its households, "
                     "firms and state save against what everyone borrows; your own rate is this plus "
                     "a premium for how much of your limit you use, less your standing",
        }
