"""One civilisation's economy, a year at a time (the order is in protocols.py).

`Economy(setup)` opens it; `Economy(setup, EconomyRecord.from_record(saved))` resumes it.
`step(inputs)` runs a year and returns what the engine reads back.
"""
import math
from dataclasses import dataclass, field
from typing import Dict

from . import credit, producers, unit_cost
from .market_areas import AreaMap
from .market_memory import YearView
from .opening import open_economy
from .protocols import YearInputs
from .record import EconomyRecord
from .setup import EconomySetup, labour_area
from .tile_costs import carriage_table
from .types import Bid, EDGE_CONSUMPTION, GoodsMove, is_edge
from .year_close import (check_money, close_agents, dispatch_merchants, money_taxes, national_prices,
                         remember_price_level, wear_and_spoilage)
from .year_goods import (add_orders, clear_goods, cohort_orders, merchant_orders, mint_orders, state_orders)
from .year_labour import clear_labour, labour_offers, move_workers, subsistence_cost_by_tile
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
        offers = labour_offers(setup, record, view, subsistence_cost_by_tile(setup, record, view))
        clear_labour(setup, record, labour_bids, offers, ledger)
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
        if not requests or not funds:
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
            recipe = setup.recipes[producer.recipe_id]
            for good, per_run in sorted(recipe.plant_goods.items()):
                price = view.price(good, view.area_of(good, producer.tile)) if good in self.area_map.goods() else None
                if not price:
                    continue
                area = view.area_of(good, producer.tile)
                # no dearer than the price at which the new plant would earn just the loan's rate
                order_book.setdefault((good, area), ([], []))[0].append(
                    Bid(producer.agent_id, good, area, producer.tile, per_run * funded_runs, 0.0, price, 0.0,
                        loan.principal, maximum_price=price * max(1.0, worth.get(loan.borrower, 1.0))))
        record.expansion_runs = {}
        return plant_runs

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
