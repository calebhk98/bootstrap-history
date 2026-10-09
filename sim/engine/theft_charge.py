"""Theft applied to actors: each year a holder loses what thieves can take of everything it keeps.

The thieves are a named edge (`edge:thieves`). Stolen money leaves the holder's purse for the edge, so the total
is conserved; stolen goods leave the holder's stock for the edge's goods; land cannot be carried off. Coin is lost
in full, a loan or a share is lost as the payments a thief diverts, paid from the purse and never beyond it.
Sack and banditry (`society_hazards.py`) are larger thefts priced by the same exposure (`plunder_founder`).
"""
from sim.agents.api import edges, ledger

from . import theft_exposure
from .coin_hoard import COIN_GUARD_HOURS_PER_TONNE_YEAR
from .holdings_exposure import HoldingsExposureMixin

THEFT_CAUSE = "theft"
# Coin is guarded by the keeping cost already charged; stock is watched by nobody.
GUARDED_KINDS = ("coin",)


class TheftChargeMixin(HoldingsExposureMixin):
    """Mixed into `Sim`."""

    def steal_from(self, holder, exposure, strength, guard_hours_per_tonne_year, visible_scale, state_capacity,
                   protection, cause=THEFT_CAUSE):
        """Thieves take a theft of this strength from what the holder keeps: money to the thieves' edge, goods
        out of its stock to the edge's goods. Returns the money taken, never more than the purse."""
        shares = theft_exposure.theft_shares_by_kind(exposure.values, strength, guard_hours_per_tonne_year,
                                                     visible_scale, state_capacity, protection)
        thieves = self.edge(edges.EDGE_THIEVES)
        for lot in exposure.lots:
            tonnes = min(lot.tonnes, lot.tonnes * shares.get("goods", 0.0))
            if tonnes > 0.0:
                lot.take(tonnes)
                thieves.receive_goods(lot.name, tonnes)
        wanted = sum(max(0.0, value) * shares[kind] for kind, value in exposure.values.items()
                     if kind not in ("goods", "land"))
        taken = min(wanted, exposure.purse)
        if taken > 0.0:
            ledger.transfer(holder, thieves, taken, cause)
        return taken

    def charge_actors_for_theft(self):
        """Every home-country actor in business (a state, a firm) loses its expected theft of what it keeps.
        Guarding is the keeping cost `charge_actors_for_keeping_coin` charges in full; the state's order is
        the country's state capacity."""
        from .agents_port import SimWorld
        world = SimWorld(self)
        for actor in self.actors.actors.values():
            record = actor.record
            if record.exited_year is not None or record.stratum:
                continue
            if record.country not in (None, self.actors.state.home_country):
                continue
            exposure = self.actor_exposure(actor, world.material_price, self.actors.get)
            if not exposure.values:
                continue
            scale = self.visible_scale(sum(actor.workforce.values()), record.money, actor.prominence())
            self.steal_from(actor, exposure, theft_exposure.THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE,
                            {kind: COIN_GUARD_HOURS_PER_TONNE_YEAR for kind in GUARDED_KINDS}, scale,
                            self.state_capacity, 0.0)

    def founder_visible_scale(self):
        household = self.state.household
        return self.visible_scale(self.labour.headcount(), household.capital, household.eminence)

    def charge_founder_for_theft(self, keeping_paid, keeping_owed):
        """The founder's household loses its expected theft; its guarding counts for the share of the keeping
        cost its purse could pay."""
        household = self.state.household
        paid_share = keeping_paid / keeping_owed if keeping_owed > 0.0 else 0.0
        guard = {kind: COIN_GUARD_HOURS_PER_TONNE_YEAR * paid_share for kind in GUARDED_KINDS}
        return self.steal_from(household, self.founder_exposure(),
                               theft_exposure.THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE, guard,
                               self.founder_visible_scale(), self.state_capacity, household.protection)

    def plunder_founder(self, strength, cause, order_holds):
        """A sack or a bandit year takes from the founder by the same exposure: what is portable and visible,
        less what is guarded. A sack comes where order has failed (`order_holds` False). Returns the money taken."""
        household = self.state.household
        if order_holds:
            capacity, protection = self.state_capacity, household.protection
        else:
            capacity, protection = 0.0, 0.0
        guard = {kind: COIN_GUARD_HOURS_PER_TONNE_YEAR for kind in GUARDED_KINDS}
        return self.steal_from(household, self.founder_exposure(), strength, guard, self.founder_visible_scale(),
                               capacity, protection, cause)
