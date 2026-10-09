"""Theft applied to actors: each year a holder that keeps coin loses its expected theft to the thieves.

The thieves are a named edge (`edge:thieves`): the money leaves the holder's purse and stays in the economy, so
the total is conserved. This is the standing, small-scale loss; `SACK_CAPITAL_LOSS` and `BANDITRY_CAPITAL_LOSS`
(`society_hazards.py`) stay as wartime and frontier events that take a large share at once. Only money moves
through the ledger, so the engine passes the coin an actor holds; goods, land and loans are priced by
`theft_exposure` for any caller that can pass them, and no actor exposes them yet.
"""
from sim.agents.api import edges, ledger

from . import theft_exposure
from .coin_hoard import COIN_GUARD_HOURS_PER_TONNE_YEAR

THEFT_CAUSE = "theft"


class TheftChargeMixin:
    """Mixed into `Sim`."""

    def steal_from(self, holder, holdings, guard_hours_per_tonne_year, visible_scale, state_capacity, protection):
        """Move the expected theft of the holder's coin to the thieves; returns the amount, never more than the
        coin held."""
        coin = max(0.0, holdings.get("coin", 0.0))
        loss = theft_exposure.expected_theft_loss({"coin": coin}, guard_hours_per_tonne_year, visible_scale,
                                                  state_capacity, protection)
        if loss > 0.0:
            ledger.transfer(holder, self.edge(edges.EDGE_THIEVES), loss, THEFT_CAUSE)
        return loss

    def charge_actors_for_theft(self):
        """Every home-country actor in business that holds money (a state, a firm) loses its expected theft.
        Guarding is the keeping cost `charge_actors_for_keeping_coin` charges in full; the state's order is
        the country's state capacity."""
        for actor in self.actors.actors.values():
            record = actor.record
            if record.exited_year is not None or record.money <= 0.0 or record.stratum:
                continue
            if record.country not in (None, self.actors.state.home_country):
                continue
            scale = self.visible_scale(sum(actor.workforce.values()), record.money, actor.prominence())
            self.steal_from(actor, {"coin": record.money}, COIN_GUARD_HOURS_PER_TONNE_YEAR, scale,
                            self.state_capacity, 0.0)

    def charge_founder_for_theft(self, keeping_paid, keeping_owed):
        """The founder's household loses its expected theft; its guarding counts for the share of the keeping
        cost its purse could pay."""
        household = self.state.household
        paid_share = keeping_paid / keeping_owed if keeping_owed > 0.0 else 0.0
        scale = self.visible_scale(self.labour.headcount(), household.capital, household.eminence)
        return self.steal_from(household, {"coin": household.capital}, COIN_GUARD_HOURS_PER_TONNE_YEAR * paid_share,
                               scale, self.state_capacity, household.protection)
