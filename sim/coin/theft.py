"""Theft applied to holders: each year a holder loses what thieves can take of everything it keeps.

The thieves are a named edge (`edge:thieves`). Stolen money leaves the holder's purse for the edge, so the total is
conserved; stolen goods leave the holder's stock for the edge's goods; land cannot be carried off. Coin is lost in
full, a loan or a share is lost as the payments a thief diverts, paid from the purse and never beyond it. Sack and
banditry are larger thefts priced by the same exposure (`plunder_household`)."""
from typing import Optional

from sim.agents.api import edges, joint_stock
from sim.labour.api import wage_provider
from sim.actors.api import DrawDownActorStore, HoldEdgeGoods
from sim.demography.api import TakeFromGranary
from sim.ledger.api import STORE_ACTOR, STORE_GRANARY, STORE_STOCK, DrawDownStock, PayEdge, PayEdgeFrom

from . import exposure as exposures
from . import theft_exposure
from .constants import COIN_GUARD_HOURS_PER_TONNE_YEAR, GUARDED_KINDS, THEFT_CAUSE


class Theft:
    """The exposure views and the theft commands (needs: civilisation, acting_balance, lent_share, held_goods, goods_quote,
    farm_holdings, farm_land_price, forest_holding, headcount, eminence, standing, visible_scale, order_reach,
    cast, actor_world; sends PayEdge, PayEdgeFrom, DrawDownStock, DrawDownActorStore, TakeFromGranary, HoldEdgeGoods)."""

    def household_exposure(self):
        """What the acting household keeps: purse, material stock and granary, farm and forest land."""
        purse, lent_share = self.needs.acting_balance(), self.needs.lent_share()
        stock = self.needs.held_goods()
        quotes = {key: self.needs.goods_quote[key] for key in sorted(stock)}
        staple_name = wage_provider.staple_material(self.needs.civilisation())
        staple_quote = self.needs.goods_quote[staple_name]
        farm = self.needs.farm_holdings()
        forest = self.needs.forest_holding()
        land = exposures.land_value(farm["hectares"], self.needs.farm_land_price(), forest["hectares"],
                                    forest["base_cost_per_hectare"], forest["price_index"])
        return exposures.household_exposure(purse, lent_share, stock, quotes, staple_name, staple_quote,
                                            farm["stock_kg"], land)

    def household_visible_scale(self):
        return self.needs.visible_scale(self.needs.headcount(), self.needs.acting_balance(), self.needs.eminence())

    def steal_from(self, holder: Optional[str], exposure, strength, guard_hours_per_tonne_year, visible_scale, state_reach,
                   protection, cause=THEFT_CAUSE):
        """Thieves take a theft of this strength from what the holder keeps: money to the thieves' edge, goods out of
        its stock to the edge's goods. `holder` is an actor's id, or None for the acting household. Returns the money
        taken, never more than the purse."""
        shares = theft_exposure.theft_shares_by_kind(exposure.values, strength, guard_hours_per_tonne_year,
                                                     visible_scale, state_reach, protection)
        for lot in exposure.lots:
            tonnes = min(lot.tonnes, lot.tonnes * shares.get("goods", 0.0))
            if tonnes > 0.0:
                self.take_goods(lot, tonnes)
        wanted = sum(max(0.0, value) * shares[kind] for kind, value in exposure.values.items()
                     if kind not in ("goods", "land"))
        taken = min(wanted, exposure.purse)
        if taken > 0.0:
            if holder is None:
                self.needs.send(PayEdge(edges.EDGE_THIEVES, taken, cause))
            else:
                self.needs.send(PayEdgeFrom(holder, edges.EDGE_THIEVES, taken, cause))
        return taken

    def take_goods(self, lot, tonnes):
        """Thieves take tonnes of a good out of the holder's store it sits in, never below zero, into the thieves' edge's goods."""
        if lot.store == STORE_ACTOR:
            self.needs.send(DrawDownActorStore(lot.actor, lot.name, tonnes))
        elif lot.store == STORE_STOCK:
            self.needs.send(DrawDownStock(lot.name, tonnes))
        elif lot.store == STORE_GRANARY:
            self.needs.send(TakeFromGranary(tonnes * 1000.0))   # the granary counts kilograms
        self.needs.send(HoldEdgeGoods(edges.EDGE_THIEVES, lot.name, tonnes))

    def charge_actors_theft(self, command):
        """Every home-country actor in business (a state, a firm) loses its expected theft of what it keeps. Guarding is
        the keeping cost `ChargeKeeping` charges in full; the state's order is the share of its people its employed
        guards watch."""
        registry, world = self.needs.cast(), self.needs.actor_world()
        lent_share = self.needs.lent_share()   # theft moves coin out of purses, never into a loan: one reading serves every actor
        for actor_id, actor in sorted(registry.actors.items()):  # id order, as a loaded game wraps them
            record = actor.record
            if record.exited_year is not None or record.stratum:
                continue
            if record.country not in (None, registry.state.home_country):
                continue
            exposure = exposures.actor_exposure(
                actor_id, actor.money, record.stores, world.material_price,
                lambda record=record: joint_stock.shares_worth(record.holdings, registry.get), lent_share)
            if not exposure.values:
                continue
            scale = self.needs.visible_scale(sum(actor.workforce.values()), actor.money, actor.prominence())
            self.steal_from(actor_id, exposure, theft_exposure.THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE,
                            {kind: COIN_GUARD_HOURS_PER_TONNE_YEAR for kind in GUARDED_KINDS}, scale,
                            self.needs.order_reach(), 0.0)

    def charge_household_theft(self, command):
        """The household loses its expected theft; its guarding counts for the share of the keeping cost its purse could
        pay."""
        paid_share = command.keeping_paid / command.keeping_owed if command.keeping_owed > 0.0 else 0.0
        guard = {kind: COIN_GUARD_HOURS_PER_TONNE_YEAR * paid_share for kind in GUARDED_KINDS}
        return self.steal_from(None, self.household_exposure(), theft_exposure.THEFT_SHARE_PER_YEAR_AT_FULL_EXPOSURE, guard,
                               self.household_visible_scale(), self.needs.order_reach(), self.needs.standing()["protection"])

    def plunder_household(self, command):
        """A sack or a bandit year takes from the household by the same exposure: what is portable and visible, less
        what is guarded. A sack comes where order has failed. Returns the money taken."""
        if command.order_holds:
            capacity, protection = self.needs.order_reach(), self.needs.standing()["protection"]
        else:
            capacity, protection = 0.0, 0.0
        guard = {kind: COIN_GUARD_HOURS_PER_TONNE_YEAR for kind in GUARDED_KINDS}
        return self.steal_from(None, self.household_exposure(), command.strength, guard, self.household_visible_scale(),
                               capacity, protection, command.cause)
