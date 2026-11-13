"""The opening's final demand over arrays: what the households of a settlement buy at an income, packed once per solve.

`opening._settle_income` asks for the final demand at many incomes. Between the asks the prices, the baskets, the stores'
weights and the plots' units (for one share of hours hired) do not move; only the incomes do. `OpeningDemand` packs the
cohorts, their needs, goods and store goods when the solve starts and asks the kernel (`opening_demand_kernel.demand`) for
every cohort at once. The rules are the ones `opening._final_demand` runs through `OwnPlots.resting_orders`; a settlement
the kernel does not cover (a need with share limits, a durable already held in the store) is left to that path (`supported` is false)."""
import math
from typing import Dict, List, Optional

import numpy as np

from sim.world import need_basket
from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD

from . import household_grown_floors, households_buffer_stock, households_orders, households_store, opening_demand_kernel as kernel, opening_own
from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE


def constants() -> np.ndarray:
    """The rule constants the kernel reads, from the modules that declare them."""
    values = np.zeros(kernel.K_COUNT)
    values[kernel.K_FLOOR_MARGIN] = households_orders.FLOOR_BUDGET_PRICE_MARGIN
    values[kernel.K_SAFETY] = households_orders.BUDGET_SAFETY_SHARE
    values[kernel.K_DRAWDOWN] = households_orders.WEALTH_DRAWDOWN_LIMIT
    values[kernel.K_CUT] = households_orders.SPENDING_CUT_LIMIT
    values[kernel.K_CASH_SHARE] = households_buffer_stock.yearly_cash_share()
    values[kernel.K_WEALTH_TARGET] = households_buffer_stock.WEALTH_INCOME_RATIO_TARGET / households_buffer_stock.MONTHS_PER_YEAR
    values[kernel.K_STORE_LIMIT] = households_store.STORE_SHARE_LIMIT
    values[kernel.K_STORE_SHARE] = households_store.STORE_SAVINGS_SHARE
    values[kernel.K_TIME_PREFERENCE] = HOUSEHOLD_TIME_PREFERENCE
    values[kernel.K_BAND] = households_store.STORE_REBALANCE_BAND
    values[kernel.K_HOUSEHOLD_SIZE] = PERSONS_PER_HOUSEHOLD
    return values


class OpeningDemand:
    """The packed cohorts of one settlement, and the units their plots grew at the last share of hours hired."""

    def __init__(self, parts, view, specs, own, replacement: float = 0.0, backing_good=None, capital_tile=None,
                 stationary: bool = True) -> None:
        """`parts` is (cohort, basket, priced needs, the store dict its basket shares) for each cohort of the settlement;
        `replacement` of the metal `backing_good` is bought for the mint, at the `capital_tile`, on top of what the cohorts buy."""
        self.view = view
        self.specs = specs
        self.own = own
        self.stationary = stationary
        self.replacement = replacement
        self.backing_good = backing_good
        self.capital_tile = capital_tile
        parts = sorted(parts, key=lambda part: part[0].agent_id)
        self.cohorts = [part[0] for part in parts]
        self.baskets = [part[1] for part in parts]
        self.priced = [part[2] for part in parts]
        self.stores = [part[3] for part in parts]
        self.supported = True
        self._pack()
        self._solver = None
        self._grown_for = None      # share of hours hired the units were worked out at
        self._own_work: Dict[str, float] = {}
        self.final = np.zeros((len(self.tiles), len(self.goods)))
        self.stamp = np.full(self.final.shape, -1, dtype=np.int64)

    @classmethod
    def of_settlement(cls, setup, record, view, memory, own, replacement: float = 0.0, stationary: bool = True):
        """The settlement's cohorts, with the baskets, priced needs and store dicts the bid memory holds for them."""
        parts = []
        for cohort in record.cohorts.values():
            basket = memory.basket(setup, record, cohort)
            parts.append((cohort, basket, memory.priced(setup, record, view, cohort, basket), memory.stores(record, cohort)))
        return cls(parts, view, setup.specs, own, replacement, record.currency.backing_good, setup.capital_tile, stationary)

    def _pack(self) -> None:
        view, specs = self.view, self.specs
        goods: Dict[str, int] = {}
        tiles: Dict[str, int] = {}

        names: List[str] = []

        def good_index(good):
            if good not in goods:
                goods[good] = len(goods)
                names.append(good)
            return goods[good]

        cohort_floats, cohort_ints, need_floats, need_ints, row_floats, row_ints, store_floats, store_ints, order = [], [], [], [], [], [], [], [], []
        unit_floor: List[float] = []
        self.unit_slots: List[Dict[str, int]] = []
        for cohort, basket, priced, shared in zip(self.cohorts, self.baskets, self.priced, self.stores):
            slots = {}
            for need in basket.needs:
                slots[need.need_id] = len(unit_floor)
                unit_floor.append(need.subsistence_per_person * cohort.people)
            self.unit_slots.append(slots)
            need0, row0, store0 = len(need_floats), len(row_floats), len(store_floats)
            tile = tiles.setdefault(cohort.tile, len(tiles))
            claims = owned = rate = 0.0
            has_rate = 0
            if priced and cohort.people > 0.0:
                if any(need.spec.share_limits for need in priced):
                    self.supported = False
                first_good = priced[0].goods[0][0]
                area_currency = view.currency_of(view.area_of(first_good, cohort.tile))
                claims = view.claims(cohort.agent_id, area_currency)
                owned = households_buffer_stock.share_wealth_carried(cohort.share_wealth, view.equity(cohort.agent_id))
                weights, store_prices, held = households_store.store_holding(cohort, view, specs, priced, shared)
                interest = view.interest_rate(area_currency)
                has_rate = 0 if interest is None else 1
                rate = 0.0 if interest is None else interest
                first_unit = {}
                for need in basket.needs:
                    for good, _effect in need.goods:
                        first_unit.setdefault(good, slots[need.need_id])
                for need in priced:
                    qualities = dict(need.spec.qualities)
                    limit = need_basket.satiation_limit(basket, need.spec.need_id, need.spec.subsistence_per_person)
                    ceilings = need.ceilings or need_basket.price_ceilings(need.goods)
                    need_ints.append([len(row_floats), len(row_floats) + len(need.goods)])
                    need_floats.append([need.price_index, need.spec.subsistence_per_person, need.spec.budget_weight,
                               math.nan if limit is None else limit, 1.0 if need.spec.subsistence_per_person > 0.0 else 0.0,
                               1.0 if need.spec.qualities else 0.0])
                    for (good, price, effect, share), ceiling in zip(need.goods, ceilings):
                        spec = specs.get(good)
                        found = view.price(good, view.area_of(good, cohort.tile))
                        row_floats.append([price, effect, share, ceiling, qualities.get(good, 1.0), view.stock(cohort.agent_id, good, cohort.tile),
                                   spec.service_life_years if spec is not None else 0.0,
                                   spec.spoilage_per_year if spec is not None else 0.0, found or 0.0,
                                   dict(need.spec.share_limits).get(good, math.nan)])
                        row_ints.append([good_index(good), first_unit.get(good, -1)])
                for good, weight in weights.items():
                    spec = specs[good]
                    if held[good] > 0.0 and spec.service_life_years > 0.0:
                        self.supported = False      # a durable in use is not wealth to spend from: the old path reads the flows for it
                    found = view.price(good, view.area_of(good, cohort.tile))
                    store_floats.append([weight, store_prices[good], held[good], found or 0.0, spec.service_life_years])
                    store_ints.append(good_index(good))
            rows = range(row0, len(row_floats))
            order.extend(sorted(rows, key=lambda row: (names[row_ints[row][0]], row)))
            cohort_floats.append([cohort.people, cohort.expected_spending, cohort.expected_floor_cost, cohort.expected_inflation,
                       cohort.cash_target, owned, claims, rate, basket.substitution])
            cohort_ints.append([need0, len(need_floats), row0, len(row_floats), store0, len(store_floats), tile, has_rate])
        if self.replacement > 0.0:
            good_index(self.backing_good)       # the metal the mint buys is part of the demand
        self.goods = sorted(goods, key=goods.get)
        self.tiles = sorted(tiles, key=tiles.get)
        self.cohort_floats = np.array(cohort_floats, dtype=np.float64).reshape(-1, kernel.CF_COUNT)
        self.cohort_ints = np.array(cohort_ints, dtype=np.int64).reshape(-1, kernel.CI_COUNT)
        self.need_floats = np.array(need_floats, dtype=np.float64).reshape(-1, kernel.NF_COUNT)
        self.need_ints = np.array(need_ints, dtype=np.int64).reshape(-1, kernel.NI_COUNT)
        self.row_floats = np.array(row_floats, dtype=np.float64).reshape(-1, kernel.RF_COUNT)
        self.row_ints = np.array(row_ints, dtype=np.int64).reshape(-1, kernel.RI_COUNT)
        self.store_floats = np.array(store_floats, dtype=np.float64).reshape(-1, kernel.SF_COUNT)
        self.store_ints = np.array(store_ints, dtype=np.int64)
        self.order = np.array(order, dtype=np.int64)
        self.unit_floor = np.array(unit_floor, dtype=np.float64)
        self.unit_grown = np.zeros(len(unit_floor))
        self.row_scratch = np.zeros((len(row_floats), kernel.W_COUNT))
        self.need_scratch = np.zeros((len(need_floats), kernel.V_COUNT))
        self.good_scratch = np.zeros((len(goods), kernel.G_COUNT))
        self.store_scratch = np.zeros((len(store_floats), kernel.T_COUNT))
        self.memo = np.zeros((len(self.cohorts), 2))
        self.partials = np.zeros((4, kernel.PARTIALS))
        self.constants = constants()

    def _units_at_share(self, record) -> None:
        """The need units each cohort's plot grows at the share of hours hired now (and what that leaves the opening
        noting about the plots), worked out again only when the share has moved."""
        own = self.own
        if self._grown_for == own.share_hired:
            return
        self.unit_grown[:] = 0.0
        for position, cohort in enumerate(self.cohorts):
            agent_id = cohort.agent_id
            cohort = record.cohorts[agent_id]
            if agent_id not in self._own_work:
                self._own_work[agent_id] = own.own_work_hours(record, cohort, self.priced[position])
            units = own.grow(record, cohort, self.priced[position], self._own_work[agent_id])
            for need_id, made in units.items():
                self.unit_grown[self.unit_slots[position][need_id]] = made
        self._grown_for = own.share_hired

    def _buy(self, record) -> None:
        """Fill `final` (tile by good) with what the cohorts buy at their incomes now, and note on `own` the value of the floors
        their plots grew (spending in kind)."""
        own = self.own
        self._units_at_share(record)
        incomes = self.incomes_now(record)
        self.final[:] = 0.0
        self.stamp[:] = -1
        kernel.demand(incomes, self.stationary, self.constants, self.cohort_floats, self.cohort_ints, self.need_floats, self.need_ints, self.row_floats, self.row_ints,
                      self.store_floats, self.store_ints, self.row_scratch, self.need_scratch, self.good_scratch, self.order, self.store_scratch, self.unit_floor, self.unit_grown,
                      self.memo, self.final, self.stamp, self.partials)
        for position, cohort in enumerate(self.cohorts):
            grown = {need_id: float(self.unit_grown[slot]) for need_id, slot in self.unit_slots[position].items()}
            met_by_need, _met_by_good = household_grown_floors.met_shares(self.baskets[position], cohort.people, grown)
            own.in_kind += household_grown_floors.floor_cost_met(self.priced[position], cohort.people, met_by_need)

    def final_demand(self, record) -> Dict[str, Dict[str, float]]:
        """What `opening._final_demand` gives for the cohorts' incomes now, without the metal the mint buys: {tile: {good: quantity}}."""
        self._buy(record)
        final: Dict[str, Dict[str, float]] = {}
        seen = np.argwhere(self.stamp >= 0)
        for tile_index, good_index in sorted(seen.tolist(), key=lambda cell: self.stamp[cell[0], cell[1]]):
            final.setdefault(self.tiles[tile_index], {})[self.goods[good_index]] = float(self.final[tile_index, good_index])
        return final

    def ask(self, record, solver, prices: Dict[str, float], hands_hours: float, passes: int, tolerance: float):
        """(the value of the final demand, the hours the runs it takes need, what their workers are paid) at the incomes now,
        after the plots' hired share has settled: each pass buys, sizes the runs that demand takes and takes the share of hours
        those runs hire, until the share moves no more than `tolerance`."""
        own = self.own
        mapping = self._mapping(solver)
        for _pass in range(passes):
            own.in_kind = 0.0
            self._buy(record)
            demand = self._demand_by_tile()
            totals = demand.cumsum(axis=0)[-1]       # tile after tile, as the dict of tiles was summed
            runs = solver.runs(solver.national_vector(mapping, totals))
            needed = math.fsum((runs * solver.hours_per_run).tolist())
            if own.note_share(opening_own.share_of_hands(needed, hands_hours)) <= tolerance:
                break
        priced = np.array([prices.get(good, 0.0) for good in self.goods])
        value = math.fsum((demand * priced).ravel().tolist())
        return value, needed, math.fsum((runs * solver.labour_cost_per_run).tolist())

    def _demand_by_tile(self) -> np.ndarray:
        """What was bought, a row for each tile in the order the old path first met it (by the first bid it made), with the metal
        the mint buys added to the capital's row (a row of its own, last, where nobody bought there)."""
        first = np.where(self.stamp >= 0, self.stamp, np.iinfo(np.int64).max).min(axis=1)
        rows = [self.final[tile].copy() for tile in np.argsort(first, kind="stable") if first[tile] < np.iinfo(np.int64).max]
        if self.replacement > 0.0:
            metal = self.goods.index(self.backing_good)
            met = [index for index, tile in enumerate(sorted((tile for tile in range(len(self.tiles)) if first[tile] < np.iinfo(np.int64).max),
                                                             key=lambda tile: (first[tile], tile))) if self.tiles[tile] == self.capital_tile]
            if met:
                rows[met[0]][metal] += self.replacement
            else:
                rows.append(np.zeros(len(self.goods)))
                rows[-1][metal] = self.replacement
        return np.array(rows).reshape(-1, len(self.goods))

    def _mapping(self, solver):
        if self._solver is not solver:
            self._solver = solver
            self._mapped = solver.mapping(self.goods)
        return self._mapped

    def incomes_now(self, record) -> np.ndarray:
        return np.array([record.cohorts[cohort.agent_id].last_year_income for cohort in self.cohorts])

    def asked_at_incomes_now(self, record) -> bool:
        """Whether the last ask was made at the incomes the cohorts hold now."""
        return bool(np.all(self.memo[:, 0] > 0.0) and np.all(self.memo[:, 1] == self.incomes_now(record)))

    def durable_bids(self, record, stationary: bool = False) -> List[tuple]:
        """(cohort, good, quantity) of each bid for a durable that serves a need (no store, no plot cut) the cohorts make holding
        exactly their incomes, in the order the bids are met: what `_opening_bids` gives for them."""
        quantity = np.zeros(len(self.row_floats))
        kernel.uncut(self.incomes_now(record), stationary, self.constants, self.cohort_floats, self.cohort_ints,
                     self.need_floats, self.need_ints, self.row_floats, self.row_ints, self.store_floats, self.store_ints,
                     self.row_scratch, self.need_scratch, self.good_scratch, self.order, self.store_scratch,
                     np.zeros(len(self.unit_floor)), np.zeros(len(self.unit_floor)), quantity, self.partials)
        found = []
        for position, cohort in enumerate(self.cohorts):
            for index in range(self.cohort_ints[position, kernel.CI_ROW0], self.cohort_ints[position, kernel.CI_ROW1]):
                row = self.order[index]
                if (quantity[row] > 0.0 and self.row_floats[row, kernel.RF_LIFE] > 0.0
                        and self.row_floats[row, kernel.RF_GPRICE] > 0.0):
                    found.append((record.cohorts[cohort.agent_id], self.goods[self.row_ints[row, kernel.RI_GOOD]], float(quantity[row])))
        return found

    def repacked(self) -> "OpeningDemand":
        """The same cohorts packed again from the stock they hold now, keeping the incomes the last ask was made at."""
        fresh = OpeningDemand(list(zip(self.cohorts, self.baskets, self.priced, self.stores)), self.view, self.specs, self.own,
                              self.replacement, self.backing_good, self.capital_tile, self.stationary)
        fresh.memo[:] = self.memo
        fresh._own_work = self._own_work
        return fresh
