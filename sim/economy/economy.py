"""One civilisation's economy, a year at a time (the order is in protocols.py).

`Economy(setup)` opens it; `Economy(setup, EconomyRecord.from_record(saved))` resumes it.
`step(inputs)` runs a year and returns what the engine reads back.
"""
import math
from dataclasses import dataclass, field
from typing import Dict, Optional

from . import credit, labour, producers, unit_cost
from .market_areas import AreaMap
from .market_memory import YearView
from .households_own import hours_for_own_plan, own_production, own_production_options, withhold_hours
from .opening import open_economy
from .protocols import YearInputs
from .record import EconomyRecord
from .setup import EconomySetup, labour_area
from .tile_costs import carriage_table
from .types import Bid, EDGE_CONSUMPTION, GoodsMove, is_edge
from .year_close import (check_money, close_agents, dispatch_merchants, money_taxes, national_prices,
                         remember_price_level, wear_and_spoilage)
from .year_goods import (add_orders, clear_goods, cohort_orders, merchant_orders, mint_orders, state_orders)
from .year_labour import clear_labour, labour_offers, move_workers, outside_option_by_tile
from .year_ledger import YearLedger


@dataclass
class YearOutcome:
    year: int
    price_level: float
    prices: Dict[str, float]                       # each good's price over its areas, by volume
    wages: Dict[str, float]                        # each trade's mean wage per hour over its areas
    rate: float
    money_supply: float
    hunger_by_tile: Dict[str, float] = field(default_factory=dict)   # food floor units short
    output: Dict[str, float] = field(default_factory=dict)
    idle_hours: float = 0.0
    vacant_hours: float = 0.0
    conservation_residual: float = 0.0
    state_cash: float = 0.0


class Economy:
    def __init__(self, setup: EconomySetup, record: EconomyRecord = None) -> None:
        self.setup = setup
        if record is None:
            record, area_map, carriage = open_economy(setup)
        else:
            carriage = carriage_table(setup.tiles, setup.carriage_rates, setup.handling_rates, edges=setup.edges)
            area_map = AreaMap(setup.tiles, carriage,
                               [(setup.specs[good], price) for good, price in sorted(setup.opening_prices.items())
                                if good in setup.specs and price > 0.0],
                               setup.opening_population_by_tile)
        self.record = record
        self.area_map = area_map
        self.carriage = carriage
        self._own_options = None

    def view(self) -> YearView:
        return YearView(self.record.memory, self.record.book, self.area_map, self.setup.currency_id, labour_area)

    def step(self, inputs: YearInputs) -> YearOutcome:
        setup, record = self.setup, self.record
        record.book.start_year()
        ledger = YearLedger()
        self._follow_population(inputs)
        self._follow_yields(inputs)
        view = self.view()
        money = setup.currency_id
        plans = {producer_id: producers.plan(producer, setup.recipes[producer.recipe_id], view,
                                             record.book.balance(producer_id, money))
                 for producer_id, producer in sorted(record.producers.items())}
        labour_bids = [bid for plan in plans.values() for bid in plan.labour_bids]
        for orders in inputs.engine_orders.values():
            labour_bids.extend(orders.labour_bids)
        offers, kept = withhold_hours(labour_offers(setup, record, view, outside_option_by_tile(setup, record, view)),
                                      self._shortfall_hours())
        clear_labour(setup, record, labour_bids, offers, ledger)
        self._grow_own(offers, ledger, inputs.harvest_factor, kept)
        self._service_loans(view.year)
        order_book = {}
        funds = cohort_orders(setup, record, view, ledger, order_book)
        merchant_orders(setup, record, view, self.area_map, self.carriage, order_book)
        state_orders(setup, record, view, self.area_map, order_book, {})
        mint_orders(setup, record, self.area_map, order_book)
        for agent, orders in sorted(inputs.engine_orders.items()):
            add_orders(order_book, orders)
        for plan in plans.values():
            for bid in plan.bids:
                order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
        plant_runs = self._lend(funds, view, order_book)
        for producer_id, runs in self._rebuild_worn_plant(view, order_book).items():
            plant_runs[producer_id] = plant_runs.get(producer_id, 0.0) + runs
        clear_goods(setup, record, view, self.area_map, order_book, plans, ledger)
        dispatch_merchants(setup, record, self.carriage, ledger)
        money_taxes(setup, record, view, ledger)
        self._build_plant(plant_runs)
        close_view = YearView(record.memory, record.book, self.area_map, money, labour_area)
        close_agents(setup, record, close_view, ledger, self.area_map)
        move_workers(setup, record, ledger)
        wear_and_spoilage(setup, record)
        level = remember_price_level(setup, record)
        record.memory.year += 1
        return self._outcome(ledger, level)

    # ---- the year's pieces ------------------------------------------------------------------
    def _follow_population(self, inputs: YearInputs) -> None:
        """Cohorts and workforce follow the engine's people per tile."""
        if not inputs.population_by_tile:
            return
        record = self.record
        people_now: Dict[str, float] = {}
        for cohort in record.cohorts.values():
            people_now[cohort.tile] = people_now.get(cohort.tile, 0.0) + cohort.people
        for cohort_id, cohort in sorted(record.cohorts.items()):
            before = people_now.get(cohort.tile, 0.0)
            after = inputs.population_by_tile.get(cohort.tile, before)
            if before <= 0.0 or after == before:
                continue
            scale = after / before
            record.cohorts[cohort_id] = type(cohort)(**{**cohort.__dict__, "people": cohort.people * scale,
                                                        "working_people": cohort.working_people * scale})
        for tile, workforce in record.workforce.items():
            before = people_now.get(tile, 0.0)
            after = inputs.population_by_tile.get(tile, before)
            if before > 0.0 and after != before:
                for trade in workforce:
                    workforce[trade] *= after / before

    def _follow_yields(self, inputs: YearInputs) -> None:
        for producer_id, factor in inputs.yield_factor_by_producer.items():
            producer = self.record.producers.get(producer_id)
            if producer is not None and producer.yield_factor != factor:
                self.record.producers[producer_id] = type(producer)(**{**producer.__dict__, "yield_factor": factor})

    def _own_plot_options(self):
        if self._own_options is None:
            setup = self.setup
            self._own_options = own_production_options(setup.recipes, setup.land_per_run, setup.basket)
        return self._own_options

    def _shortfall_hours(self) -> Dict[str, float]:
        """Hours each cohort keeps back for its own-plot plan, at the tile's usual fertility (it plants
        before it knows the harvest)."""
        hours = {}
        for cohort_id, cohort in sorted(self.record.cohorts.items()):
            tile = self.setup.tiles.get(cohort.tile)
            hours[cohort_id] = hours_for_own_plan(cohort, self._own_plot_options(),
                                                        tile.fertility if tile else 0.0)
        return hours

    def _grow_own(self, offers, ledger: YearLedger, harvest_factor: float = 1.0,
                  kept: Optional[Dict[str, float]] = None) -> None:
        """Hours kept back and hours nobody hired go into the household's own plot (households_own.py)."""
        setup, record = self.setup, self.record
        self._own_plot_options()
        kept = kept or {}
        offered: Dict[str, float] = {}
        for offer in offers:
            offered[offer.worker] = offered.get(offer.worker, 0.0) + offer.hours
        for cohort_id, cohort in sorted(record.cohorts.items()):
            idle = offered.get(cohort_id, 0.0) + kept.get(cohort_id, 0.0) - ledger.hours_sold.get(cohort_id, 0.0)
            tile = setup.tiles.get(cohort.tile)
            moves, grown, units = own_production(cohort, idle, self._own_options, setup.recipes,
                                                 (tile.fertility if tile else 0.0) * harvest_factor,
                                                 setup.basket_for(cohort.tile))
            if moves:
                record.book.move_many(moves)
                ledger.grown[cohort_id] = grown
                ledger.grown_units[cohort_id] = units

    def _service_loans(self, year: int) -> None:
        record = self.record
        money = self.setup.currency_id
        if not record.loans:
            return
        cash = {loan.borrower: record.book.balance(loan.borrower, money) for loan in record.loans}
        transfers, loans, _defaults = credit.service(record.loans, cash, year)
        record.book.transfer_many(transfers)
        for transfer in transfers:
            record.property_income[transfer.payee] = record.property_income.get(transfer.payee, 0.0) + transfer.amount
        record.loans = loans

    def _lend(self, funds, view, order_book) -> Dict[str, float]:
        """New loans from savings; a producer that borrowed to build bids for its plant goods."""
        record, setup = self.record, self.setup
        money = setup.currency_id
        requests, record.loan_requests = record.loan_requests, []
        if not requests:
            if funds:
                # savings on offer and nobody borrowing: lenders compete the rate down toward the lowest
                # they will lend at, at the market's usual pace
                floor = min(offer.minimum_rate for offer in funds)
                record.memory.rates[money] = labour.sticky_move(record.memory.rates.get(money), floor,
                                                                credit.RATE_ADJUSTMENT_SHARE_PER_YEAR)
            return {}
        if not funds:
            return {}
        debt: Dict[str, float] = {}
        for loan in record.loans:
            debt[loan.borrower] = debt.get(loan.borrower, 0.0) + loan.principal
        loans, rate, _unmet = credit.clear(requests, funds, money, record.memory.rates.get(money), debt,
                                           year=view.year)
        record.book.transfer_many(credit.disbursements(loans))
        record.loans.extend(loans)
        record.memory.rates[money] = rate
        asked = {request.borrower: request.amount for request in requests}
        worth = {request.borrower: request.maximum_rate / max(rate, 1e-9) for request in requests}
        plant_runs: Dict[str, float] = {}
        for loan in loans:
            producer = record.producers.get(loan.borrower)
            runs = record.expansion_runs.get(loan.borrower, 0.0)
            if producer is None or runs <= 0.0 or not asked.get(loan.borrower):
                continue
            funded_runs = runs * min(1.0, loan.principal / asked[loan.borrower])
            plant_runs[loan.borrower] = plant_runs.get(loan.borrower, 0.0) + funded_runs
            # no dearer than the price at which the new plant would earn just the loan's rate
            self._bid_for_plant(producer, funded_runs, loan.principal, worth.get(loan.borrower, 1.0), view, order_book)
        record.expansion_runs = {}
        return plant_runs

    def _rebuild_worn_plant(self, view, order_book) -> Dict[str, float]:
        """Producers that covered their costs bid, from their own cash, for the plant goods that rebuild
        what wore out last year, no dearer than the price at which the plant still earns the live rate."""
        record, setup = self.record, self.setup
        money = setup.currency_id
        rate = max(view.interest_rate(money), 1e-9)
        rebuilt: Dict[str, float] = {}
        worn, record.worn_runs = record.worn_runs, {}
        for producer_id, runs in sorted(worn.items()):
            producer = record.producers.get(producer_id)
            if producer is None or runs <= 0.0:
                continue
            recipe = setup.recipes[producer.recipe_id]
            inputs = producers.live_input_prices(producer, recipe, view)
            wages = producers.live_wages(producer, recipe, view)
            earning = unit_cost.return_on_capital(recipe, producers.expected_output_prices(producer, recipe, view),
                                                  inputs, wages)
            cash = record.book.balance(producer_id, money)
            if not earning > rate or cash <= 0.0:
                continue
            self._bid_for_plant(producer, runs, cash, earning / rate, view, order_book)
            rebuilt[producer_id] = runs
        return rebuilt

    def _bid_for_plant(self, producer, runs, budget, worth_ratio, view, order_book) -> None:
        recipe = self.setup.recipes[producer.recipe_id]
        for good, per_run in sorted(recipe.plant_goods.items()):
            if good not in self.area_map.goods():
                continue
            area = view.area_of(good, producer.tile)
            price = view.price(good, area)
            if not price:
                continue
            order_book.setdefault((good, area), ([], []))[0].append(
                Bid(producer.agent_id, good, area, producer.tile, per_run * runs, 0.0, price, 0.0,
                    budget, maximum_price=price * max(1.0, worth_ratio)))

    def _build_plant(self, plant_runs: Dict[str, float]) -> None:
        """Plant goods a producer received are built in; capacity grows by the share that arrived."""
        record, setup = self.record, self.setup
        for producer_id, runs in sorted(plant_runs.items()):
            producer = record.producers.get(producer_id)
            if producer is None:
                continue
            recipe = setup.recipes[producer.recipe_id]
            share = 1.0
            moves = []
            for good, per_run in sorted(recipe.plant_goods.items()):
                wanted = per_run * runs
                held = record.book.stock(producer_id, good, producer.tile)
                used = min(wanted, held)
                share = min(share, used / wanted if wanted > 0.0 else 1.0)
                if used > 0.0:
                    moves.append(GoodsMove(producer_id, EDGE_CONSUMPTION, good, producer.tile, used, "built into plant"))
            record.book.move_many(moves)
            record.producers[producer_id] = producers.with_capacity(producer, producer.capacity_runs + runs * share)

    def _outcome(self, ledger: YearLedger, level: float) -> YearOutcome:
        record, setup = self.record, self.setup
        money = setup.currency_id
        wages: Dict[str, list] = {}
        idle = vacant = 0.0
        for result in ledger.labour_results:
            wages.setdefault(result.trade, []).append((result.wage, result.hours_hired))
            idle += result.idle_hours
            vacant += result.vacant_hours
        mean_wages = {trade: (math.fsum(wage * hours for wage, hours in rows) / math.fsum(hours for _w, hours in rows)
                              if math.fsum(hours for _w, hours in rows) > 0.0 else rows[0][0])
                      for trade, rows in sorted(wages.items())}
        hunger: Dict[str, float] = {}
        for cohort in record.cohorts.values():
            short = cohort.unmet_floor_by_need.get("food", 0.0)
            if short > 0.0:
                hunger[cohort.tile] = hunger.get(cohort.tile, 0.0) + short
        output: Dict[str, float] = {}
        for (_agent, good), quantity in ledger.output.items():
            output[good] = output.get(good, 0.0) + quantity
        return YearOutcome(year=record.memory.year, price_level=level, prices=national_prices(record),
                           wages=mean_wages, rate=record.memory.rates.get(money, 0.0),
                           money_supply=record.book.money_supply(money), hunger_by_tile=hunger,
                           output=dict(sorted(output.items())), idle_hours=idle, vacant_hours=vacant,
                           conservation_residual=check_money(record),
                           state_cash=record.book.balance(setup.state_agent, money))
