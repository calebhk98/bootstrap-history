"""One civilisation's economy, a year at a time (the order is in protocols.py).

`Economy(setup)` opens it; `Economy(setup, EconomyRecord.from_record(saved))` resumes it.
`step(inputs)` runs a year and returns what the engine reads back.
"""
import dataclasses
import math
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

from sim.world import capital_market

from . import taxes, bondage, bonded_purchase, banks, carriage_hours, credit, debt_relief, credit_claims, currency, equity, labour, land_market, lending, merchants_credit, producers, shares, sites, state_budget, tax_farming, titles_inheritance, titles_worked, unit_cost
from .credit_view import CreditView
from .market_areas import AreaMap
from .market_areas_follow import follow
from .market_memory import YearView
from .mint import mint_orders, settle_mint, staff as staff_mint
from .mint_labour import close_year as close_mint_year, mint_agent
from .money_audit import MoneyAudit, year_report
from .flow_rates import flow_imbalance
from .entry_year import close_idle_producers, open_entrants, restake_owners
from . import household_work_year
from .households_own import (hours_for_own_plan, own_production, own_production_options, plot_hectares,
                             withhold_hours)
from .labour_inputs import labour_context
from .labour_state import scale_people
from .opening import open_economy
from .protocols import YearInputs
from .record import EconomyRecord
from .setup import EconomySetup, labour_area
from .types import Bid, EDGE_CONSUMPTION, GoodsMove, is_edge
from .year_close import (check_money, close_agents, dispatch_merchants, money_taxes, national_prices,
                         remember_basket_price_level, wear_and_spoilage)
from .year_goods import add_orders, clear_goods, cohort_orders, merchant_orders, state_orders
from .year_labour import clear_labour, held_share_by_area, labour_offers, outside_option_by_tile
from .year_accounts import YearAccounts, build as build_accounts, stocks as stocks_held
from .standing_demand import with_standing_bids
from .year_ledger import YearLedger
from .collection_paused import collection_paused
from .replaced import replaced


@dataclass
class YearOutcome:
    year: int
    basket_price_level: float
    prices: Dict[str, float]                       # each good's price over its areas, by volume
    wages: Dict[str, float]                        # each trade's mean wage per hour over its areas
    rate: float
    money_supply: float
    hunger_by_tile: Dict[str, float] = field(default_factory=dict)   # food floor units short
    output: Dict[str, float] = field(default_factory=dict)
    idle_hours: float = 0.0
    vacant_hours: float = 0.0
    hired_hours: float = 0.0
    wage_floor_per_hour: float = 0.0               # the lowest a worker's ask could fall to (labour_ask_floor.py)
    extraction: Dict[Tuple[str, str], float] = field(default_factory=dict)   # runs worked per (recipe, tile) on a site
    conservation_residual: float = 0.0
    state_cash: float = 0.0
    money_audit: Optional[MoneyAudit] = None       # where money entered and left this year
    bonded_bought: Dict[Tuple[str, str], float] = field(default_factory=dict)   # (tile, trade): bonded people bought this year
    bonded_paid: float = 0.0                       # money the buyers paid for them over the exchange edge
    accounts: Optional[YearAccounts] = None        # production, use, consumption, investment, stocks; food eaten; real wage


def plant_worth_ratio(yearly_return: float, rate: float, life_years: float) -> float:
    """What a plant earning `yearly_return` per unit of its cost for its whole life is worth, as a multiple
    of that cost, discounted at `rate`: an annuity, so a rate near zero is bounded by the plant's life. A
    plant that does not wear out has no life to bound it, so it earns no ceiling above its cost."""
    if life_years <= 0.0:
        return 1.0
    if rate <= 1e-9:
        return yearly_return * life_years
    return yearly_return * -math.expm1(-life_years * math.log1p(rate)) / rate


class Economy:
    def __init__(self, setup: EconomySetup, record: EconomyRecord = None) -> None:
        self.setup = setup
        if record is None:
            record, area_map, carriage = open_economy(setup)
        else:
            carriage = setup.carriage_table(record.ways, record.area_imbalance)
            area_map = setup.area_map(carriage)
        self.record = record
        self.area_map = area_map
        self.carriage = carriage
        self.improvements: Dict[str, Dict[str, Any]] = dict(record.ways)   # the ways `carriage` and the areas were built with
        self.watched_tiles: Tuple[str, ...] = ()   # tiles whose market books are kept beside the port's and the capital's; not saved
        self._own_options = None
        self._own_hectares: Dict[str, float] = {}   # land households' own plots took this year, by tile

    def set_improvements(self, improvements: Mapping[str, Mapping[str, Any]]) -> bool:
        """Rebuild the carriage table over these built ways, partition the market areas again over it and
        carry the markets' memory to the new areas; False when they are the ways it already has."""
        if dict(improvements) == self.improvements:
            return False
        self.improvements = {key: dict(way) for key, way in improvements.items()}
        self.record.ways = {key: dict(way) for key, way in self.improvements.items()}
        return self._rebuild_carriage()

    def _rebuild_carriage(self) -> bool:
        """Carriage over the current ways and return trips, the market areas partitioned again over it, the
        markets' memory carried to the new areas."""
        self.carriage = self.setup.carriage_table(self.improvements, self.record.area_imbalance)
        area_map = self.setup.area_map(self.carriage)
        follow(self.record, self.area_map, area_map)
        self.area_map = area_map
        return True

    def rebuild_market_areas(self) -> None:
        """Partition the market areas again over the setup's goods (goods the setup gained are new markets)."""
        self.__dict__.pop("_port_shares", None)
        self._rebuild_carriage()

    def follow_flows(self) -> bool:
        """Price the carriage by last year's flows: where the opposite flow fills more of the carriers'
        return trips, a tonne costs less. False when the (stepped) emptiness of the returns is unchanged."""
        imbalance = flow_imbalance(self.record)
        if imbalance == self.record.area_imbalance:
            return False
        self.record.area_imbalance = imbalance
        return self._rebuild_carriage()

    def view(self) -> YearView:
        return CreditView(self.record.memory, self.record.book, self.area_map, self.setup.currency_id, labour_area,
                          loans=lambda: self.record.loans, equity=self._equity_read,
                          loss_rates=lambda: self.record.loss_rates)

    def _equity_read(self, view) -> Dict[str, float]:
        return equity.holdings(self.setup, self.record, view)

    def strike_lighter_coin(self, cut_share: float, restrike_share: float) -> None:
        """The issuer recoins the part of the stock that comes to the mint at `cut_share` less metal (a struck
        coin only): the metal saved is struck as more coin, which the issuer receives and spends."""
        record = self.record
        supply = record.book.money_supply(record.currency.currency_id)
        struck = currency.units_struck_by_cut(record.currency, supply, cut_share, restrike_share)
        if struck <= 0.0:
            return
        record.book.transfer_many(currency.issue(record.currency, struck, "recoinage"))
        record.currency = currency.debase_by_cut(record.currency, supply, cut_share, restrike_share)

    def step(self, inputs: YearInputs) -> YearOutcome:
        with collection_paused():
            return self._run_year(inputs)

    def _run_year(self, inputs: YearInputs) -> YearOutcome:
        if inputs.tax_rates:
            self.setup = dataclasses.replace(self.setup, tax_forms=taxes.with_rates(self.setup.tax_forms, inputs.tax_rates))
        setup, record = self.setup, self.record
        self.__dict__.pop("_port_shares", None)
        self.follow_flows()
        self.carriage.set_scale(carriage_hours.wage_scale(setup, record, self.carriage))   # the carriers' labour at the year's wage
        record.book.start_year()
        stocks_at_start = stocks_held(record.book)
        ledger = YearLedger(import_accounts=frozenset(inputs.import_accounts), export_accounts=frozenset(inputs.export_accounts))
        self._follow_population(inputs)
        self._follow_yields(inputs)
        sites.apply_site_limits(record, setup, inputs.site_limits)
        view = self.view()
        money = setup.currency_id
        debt_relief.forgive(record, inputs.debt_relief_tiles)
        tax_farming.run_auctions(setup, record, inputs.farmed_forms, record.memory.rates.get(setup.currency_id, 0.0))
        lending.lend_working_capital(setup, record, view)
        plans = {producer_id: producers.plan(producer, setup.recipes[producer.recipe_id], view,
                                             record.book.balance(producer_id, money))
                 for producer_id, producer in sorted(record.producers.items())}
        labour_bids = [bid for plan in plans.values() for bid in plan.labour_bids]
        for orders in inputs.engine_orders.values():
            labour_bids.extend(orders.labour_bids)
        state_budget.plan_year(setup, record, view, labour_bids)
        staff_mint(setup, record, view, labour_bids)
        labour_bids.extend(carriage_hours.bids(setup, record))    # merchants' carriers, from last year's shipments
        outside_option = outside_option_by_tile(setup, record, view)
        everyone = labour_offers(setup, record, view, outside_option, inputs.labour_levy_hours_per_worker)
        offers, kept = withhold_hours(everyone, self._shortfall_hours(everyone, view, outside_option))
        context = labour_context(setup, record, view, self.carriage, inputs, self._own_plot_options(), outside_option)
        labour_report = clear_labour(setup, record, labour_bids, offers, ledger, context, held_share_by_area(everyone, offers))
        ledger.bonded_bought, ledger.bonded_paid = bonded_purchase.settle(
            record.book, money, labour_report.formed, labour_bids, context.ask_floor_per_worker_year)
        self._grow_own(offers, ledger, inputs.harvest_factor, kept)
        order_book = {}
        funds = cohort_orders(setup, record, view, ledger, order_book)
        state_orders(setup, record, view, self.area_map, order_book, {})
        mint_held = mint_orders(setup, record, self.area_map, order_book,
                                ledger.hours_hired.get(mint_agent(setup), {}))
        for agent, orders in sorted(inputs.engine_orders.items()):
            add_orders(order_book, orders)
        for plan in plans.values():
            for bid in plan.bids:
                order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
        funds, pledged = banks.intermediate(setup, record, funds, view.year, inputs.institutions)
        plant_runs = self._lend(funds, view, order_book, ledger, pledged)
        merchant_orders(setup, record, view, self.area_map, self.carriage, order_book)
        for producer_id, runs in self._rebuild_worn_plant(view, order_book).items():
            plant_runs[producer_id] = plant_runs.get(producer_id, 0.0) + runs
        clear_goods(setup, record, view, self.area_map, order_book, plans, ledger, self.watched_tiles)
        settle_mint(record, mint_held)
        close_mint_year(setup, record)
        rent = land_market.settle_year(setup, record, view,
                                       {producer_id: plan.wanted_runs for producer_id, plan in plans.items()},
                                       self._own_hectares, inputs.land_tax_share_of_rent)
        interest = self._service_loans(view.year)
        bonded = bondage.service(record, money, ledger.wages_in)
        record.book.transfer_many(bonded)
        for payment in bonded:
            interest[payment.payee] = interest.get(payment.payee, 0.0) + payment.amount
        titles_inheritance.divide_estates(record)
        dispatch_merchants(setup, record, self.carriage, ledger, self.area_map)
        money_taxes(setup, record, view, ledger)
        self._build_plant(plant_runs)
        close_view = CreditView(record.memory, record.book, self.area_map, money, labour_area,
                                loans=lambda: record.loans, equity=self._equity_read,
                                loss_rates=lambda: record.loss_rates)
        close_agents(setup, record, close_view, ledger, self.area_map, self.carriage)
        open_entrants(setup, record, close_view, self.area_map, ledger.unmet_demand, self.carriage,
                      with_standing_bids(ledger.bids_by_market, inputs.standing_bids))
        restake_owners(setup, record, close_view)
        extraction = sites.extraction_by_tile(record, setup)
        close_idle_producers(setup, record)
        for lender, received in interest.items():
            record.property_income[lender] = record.property_income.get(lender, 0.0) + received
        for payment in rent:
            record.property_income[payment.payee] = record.property_income.get(payment.payee, 0.0) + payment.amount
        wear_and_spoilage(setup, record, inputs.durable_users)
        level = remember_basket_price_level(setup, record)
        record.memory.year += 1
        return self._outcome(ledger, level, extraction, stocks_at_start)

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
            record.cohorts[cohort_id] = replaced(cohort, people=cohort.people * scale,
                                                  working_people=cohort.working_people * scale)
        for tile, before in people_now.items():
            after = inputs.population_by_tile.get(tile, before)
            if before > 0.0 and after != before:
                scale_people(record.workforce, labour_area(tile), after / before)

    def _follow_yields(self, inputs: YearInputs) -> None:
        for producer_id, factor in inputs.yield_factor_by_producer.items():
            producer = self.record.producers.get(producer_id)
            if producer is not None and producer.yield_factor != factor:
                self.record.producers[producer_id] = replaced(producer, yield_factor=factor)

    def _own_plot_options(self):
        if self._own_options is None:
            setup = self.setup
            self._own_options = own_production_options(setup.recipes, setup.land_per_run, setup.basket)
        return self._own_options

    def _shortfall_hours(self, everyone=(), view=None, outside_option=None) -> Dict[str, float]:
        """Hours each cohort keeps back for its own-plot plan, at the tile's usual fertility (it plants
        before it knows the harvest), and for the household work it does itself (household_work_year.py)."""
        hours, held = {}, self._hectares_held()
        for cohort_id, cohort in sorted(self.record.cohorts.items()):
            tile = self.setup.tiles.get(cohort.tile)
            hours[cohort_id] = hours_for_own_plan(cohort, self._own_plot_options(),
                                                  tile.fertility if tile else 0.0, self.setup.recipes,
                                                  self.setup.land_per_run, held.get(cohort_id, 0.0))
        self._work_hours = {}
        if view is not None:
            self._work_hours = household_work_year.decide(self.setup, self.record, view, everyone, outside_option or {})
            for cohort_id, work in self._work_hours.items():
                hours[cohort_id] = hours.get(cohort_id, 0.0) + work
        return hours

    def _hectares_held(self) -> Dict[str, float]:
        """Hectares each cohort may work for itself: the land it holds or leases (titles, tenancies), cut to
        the tile's arable land if the claims exceed it. Decided before any growing."""
        record, held = self.record, {}
        for tile_id in sorted({cohort.tile for cohort in record.cohorts.values()}):
            tile = self.setup.tiles.get(tile_id)
            arable = tile.cropland_hectares if tile else 0.0
            asked = {cohort.agent_id: titles_worked.worked_share(record, tile_id, cohort.agent_id) * arable
                     for cohort in record.cohorts.values() if cohort.tile == tile_id}
            held.update(titles_worked.allocate_hectares(asked, arable))
        return held

    def _grow_own(self, offers, ledger: YearLedger, harvest_factor: float = 1.0,
                  kept: Optional[Dict[str, float]] = None) -> None:
        """Hours kept back and hours nobody hired go into the household's own plot (households_own.py)."""
        setup, record = self.setup, self.record
        self._own_plot_options()
        kept = kept or {}
        self._own_hectares = {}
        held = self._hectares_held()
        offered: Dict[str, float] = {}
        for offer in offers:
            offered[offer.worker] = offered.get(offer.worker, 0.0) + offer.hours
        for cohort_id, cohort in sorted(record.cohorts.items()):
            idle = (offered.get(cohort_id, 0.0) + kept.get(cohort_id, 0.0) - ledger.hours_sold.get(cohort_id, 0.0)
                    - min(kept.get(cohort_id, 0.0), getattr(self, "_work_hours", {}).get(cohort_id, 0.0)))   # household work is not spare hours
            tile = setup.tiles.get(cohort.tile)
            hours_used: Dict[str, float] = {}
            moves, grown, units = own_production(cohort, idle, self._own_options, setup.recipes,
                                                 (tile.fertility if tile else 0.0) * harvest_factor,
                                                 setup.basket_for(cohort.tile), setup.land_per_run,
                                                 held.get(cohort.agent_id, 0.0), hours_used)
            if hours_used:
                ledger.own_plot_hours[cohort_id] = hours_used
            if moves:
                record.book.move_many(moves)
                ledger.grown[cohort_id] = grown
                ledger.grown_units[cohort_id] = units
                hectares = plot_hectares(units, self._own_options, setup.recipes, setup.land_per_run,
                                         (tile.fertility if tile else 0.0) * harvest_factor)
                self._own_hectares[cohort.tile] = self._own_hectares.get(cohort.tile, 0.0) + hectares

    def _service_loans(self, year: int) -> Dict[str, float]:
        """Payments due at the year's end, out of the year's sales: before carriage, taxes and the owners'
        dividends, since a lender is paid ahead of them."""
        return lending.service(self.record, self.setup.currency_id, year, self.setup.debt_bondage_years)

    def _lend(self, funds, view, order_book, ledger, pledged=None) -> Dict[str, float]:
        """New loans from savings. A producer that borrowed to build bids for its plant goods, a household
        for its floors; a merchant's cargo is bought from its enlarged cash (merchant_orders follows)."""
        record, setup = self.record, self.setup
        money = setup.currency_id
        priced_by_tile: Dict[str, list] = {}
        requests, record.loan_requests = record.loan_requests, []
        requests = (requests + lending.household_requests(setup, record, view, ledger, priced_by_tile)
                    + lending.merchant_requests(setup, record, view, self.area_map, self.carriage))
        record.funds_offered = sum(offer.amount for offer in funds if offer.currency == money)
        record.lent_by_borrower = {}
        if not requests:
            record.expansion_runs = {}      # a working-capital loan struck ahead of the year left no plant to wait for
            if funds:
                # savings on offer and nobody borrowing: lenders compete the rate down toward the lowest
                # they will lend at, at the market's usual pace
                floor = min(offer.minimum_rate for offer in funds)
                record.memory.rates[money] = labour.sticky_move(record.memory.rates.get(money), floor,
                                                                credit.RATE_ADJUSTMENT_SHARE_PER_YEAR)
            return {}
        debt = credit_claims.principal_by_borrower(record.loans)
        loans, rate, unmet = credit.clear(requests, funds, money, record.memory.rates.get(money), debt,
                                           credit_claims.arrears_history(record.loans, record.remembered_defaults),
                                           year=view.year,
                                           rate_ceiling=capital_market.RATE_CEILING_SHARE * setup.opening_rate)
        banks.draw_deposits(record, loans, pledged or {}, view.year, money)       # a bank takes its depositors' funds for the loans it makes
        record.book.transfer_many(credit.disbursements(loans))
        record.loans.extend(loans)
        for loan in loans:
            record.lent_by_borrower[loan.borrower] = record.lent_by_borrower.get(loan.borrower, 0.0) + loan.principal
        record.memory.rates[money] = rate
        # a plant request lenders left unmet is offered to the savers as shares (the money they raise is plant like a loan's)
        raised = shares.raise_equity(record, money, unmet, funds, loans, rate, shares.rate_floor_of(setup))
        merchants_credit.stake(record.merchants, {loan.borrower: loan.principal for loan in loans})
        lending.bid_household_loans(setup, record, view, ledger, loans, order_book, priced_by_tile)
        asked = {request.borrower: request.amount for request in requests}
        worth = {}
        for request in requests:
            producer = record.producers.get(request.borrower)
            if producer is not None:
                worth[request.borrower] = plant_worth_ratio(request.maximum_rate, rate,
                                                            setup.recipes[producer.recipe_id].plant_life_years)
        plant_runs: Dict[str, float] = {}
        for borrower, principal in [(loan.borrower, loan.principal) for loan in loans] + sorted(raised.items()):
            producer = record.producers.get(borrower)
            runs = record.expansion_runs.get(borrower, 0.0)
            if producer is None or runs <= 0.0 or not asked.get(borrower):
                continue
            funded_runs = runs * min(1.0, principal / asked[borrower])
            plant_runs[borrower] = plant_runs.get(borrower, 0.0) + funded_runs
            # no dearer than the price at which the new plant would earn just the loan's rate
            self._bid_for_plant(producer, funded_runs, principal, worth.get(borrower, 1.0), view, order_book)
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
            self._bid_for_plant(producer, runs, cash, plant_worth_ratio(earning, rate, recipe.plant_life_years),
                                view, order_book)
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
            for good, per_run in recipe.plant_goods.items():
                wanted = per_run * runs
                if wanted > 0.0:
                    share = min(share, record.book.stock(producer_id, good, producer.tile) / wanted)
            # only the goods the capacity actually built uses are consumed; the rest stays in stock
            record.book.move_many([GoodsMove(producer_id, EDGE_CONSUMPTION, good, producer.tile, per_run * runs * share,
                                             "built into plant")
                                   for good, per_run in sorted(recipe.plant_goods.items()) if per_run * runs * share > 0.0])
            record.producers[producer_id] = producers.with_capacity(producer, producer.capacity_runs + runs * share)

    def _outcome(self, ledger: YearLedger, level: float, extraction, stocks_at_start) -> YearOutcome:
        record, setup = self.record, self.setup
        money = setup.currency_id
        wages: Dict[str, list] = {}
        idle = vacant = hired = 0.0
        for result in ledger.labour_results:
            wages.setdefault(result.trade, []).append((result.wage, result.hours_hired))
            hired += result.hours_hired
            idle += result.idle_hours
            vacant += result.vacant_hours
        mean_wages = {trade: (math.fsum(wage * hours for wage, hours in rows) / math.fsum(hours for _w, hours in rows)
                              if math.fsum(hours for _w, hours in rows) > 0.0 else rows[0][0])
                      for trade, rows in sorted(wages.items())}
        hunger: Dict[str, float] = {}
        for cohort in record.cohorts.values():
            short = cohort.unmet_floor_by_need.get(self.setup.hunger_need, 0.0)
            if short > 0.0:
                hunger[cohort.tile] = hunger.get(cohort.tile, 0.0) + short
        output: Dict[str, float] = {}
        for (_agent, good), quantity in ledger.output.items():
            output[good] = output.get(good, 0.0) + quantity
        record.output_by_tile = {}
        for (agent, good), quantity in sorted(ledger.output.items()):
            producer = record.producers.get(agent)
            if producer is not None and quantity > 0.0:
                row = record.output_by_tile.setdefault(producer.tile, {})
                row[good] = row.get(good, 0.0) + quantity
        prices = national_prices(record)
        return YearOutcome(year=record.memory.year, basket_price_level=level, prices=prices,
                           wages=mean_wages, rate=record.memory.rates.get(money, 0.0),
                           money_supply=record.book.money_supply(money), hunger_by_tile=hunger,
                           output=dict(sorted(output.items())), idle_hours=idle, vacant_hours=vacant, hired_hours=hired,
                           wage_floor_per_hour=ledger.wage_floor_per_hour, extraction=extraction,
                           conservation_residual=check_money(record), money_audit=year_report(record),
                           state_cash=record.book.balance(setup.state_agent, money),
                           bonded_bought=dict(ledger.bonded_bought), bonded_paid=ledger.bonded_paid,
                           accounts=build_accounts(setup, record, ledger, stocks_at_start, prices, mean_wages))
