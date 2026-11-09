"""One civilisation's economy, a year at a time (the order is in protocols.py).

`Economy(setup)` opens it; `Economy(setup, EconomyRecord.from_record(saved))` resumes it.
`step(inputs)` runs a year and returns what the engine reads back.
"""
import dataclasses
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np

from sim.world import capital_market

from .rates import own_rate
from . import cohort_people, plan_table, plan_year, producer_table
from . import outlay_room, taxes, bondage, bondage_hours, bondage_keep, bonded_purchase, banks, carriage_hours, credit, credit_idle_rate, credit_lines, debt_relief, credit_claims, currency, equity, land_market, lending, merchants_credit, producers, shares, sites, state_budget, tax_farming, titles_inheritance, titles_moves, titles_plots, unit_cost
from .credit_view import CreditView
from . import transfer_rows
from .market_areas_follow import follow
from .market_memory_areas import number_area_markets
from .market_memory import YearView, note_written
from .mint import mint_orders, settle_mint, staff as staff_mint
from .mint_labour import close_year as close_mint_year, mint_agent
from .money_audit import MoneyAudit, year_report
from .flow_rates import flow_imbalance
from .entry_year import close_idle_producers, open_entrants, restake_owners
from . import capital_year, household_offers_year, land_bid_year, land_lease_year, lend_requests
from .households_own import (hours_for_own_plan, own_production, own_production_options, plot_hectares)
from . import flight_step, households_cohort, trade_wages
from .labour_inputs import labour_context
from sim.labour.api import LabourBidTable, people_in
from .labour_state import scale_people
from .opening import open_economy
from .protocols import EconomyYearInputs
from .record import EconomyRecord
from .setup import EconomySetup, area_tile, labour_area
from .posting_sequence import post_in_order
from .types import EDGE_CONSUMPTION, GoodsMove
from .national_prices import national_prices, national_wages
from .merchants_dispatch import dispatch_merchants
from .year_arrays import YearArrays, same_source, source_of
from .year_close import close_agents, money_taxes, remember_basket_price_level, wear_and_spoilage
from .year_goods import clear_goods
from .year_order_sources import cohort_orders, merchant_orders, state_orders
from .goods_order_book import new_order_book
from .goods_order_tables import ENGINE, LOAN
from .order_rows import OrderRows
from .labour_offer_rows import LabourOfferRows
from .labour_sold_offers import sold_hours_by_worker
from .labour_supply import HourSupply
from .labour_results_table import hours_totals
from .labour_state import people_by_trade
from .year_labour import clear_labour, labour_offer_rows, outside_option_by_tile
from .year_accounts import YearAccounts, build as build_accounts, stocks as stocks_held
from .standing_demand import standing_block
from .year_ledger import YearLedger
from .collection_paused import collection_paused


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
    hired_hours: float = 0.0
    wage_floor_per_hour: float = 0.0               # the lowest a worker's ask could fall to (labour_ask_floor.py)
    extraction: Dict[Tuple[str, str], float] = field(default_factory=dict)   # runs worked per (recipe, tile) on a site
    money_audit: Optional[MoneyAudit] = None       # where money entered and left this year
    bonded_lots: list = field(default_factory=list)   # the lots bought: origin and destination tile, trade, people, the owners' ask and the carriage paid
    accounts: Optional[YearAccounts] = None        # production, use, consumption, investment, stocks; food eaten; real wage
    migrated_by_tile: Dict[str, float] = field(default_factory=dict)   # net working people the labour market moved to (+) or from (-) each tile: a request to demography, which moves the people


def plant_worth_ratio(yearly_return: float, rate: float, life_years: float) -> float:
    """What a plant earning `yearly_return` per unit of its cost for its whole life is worth, as a multiple
    of that cost, discounted at `rate`: the return over the cost's recovery factor (`capital_market.capital_recovery_factor`),
    so a rate near zero is bounded by the plant's life. A plant that does not wear out has no life to bound it,
    so it earns no ceiling above its cost."""
    if life_years <= 0.0:
        return 1.0
    return yearly_return / capital_market.capital_recovery_factor(rate, life_years)


class Economy:
    def __init__(self, setup: EconomySetup, record: EconomyRecord = None) -> None:
        self.setup = setup
        opening = record is None
        if opening:
            record, area_map, carriage = open_economy(setup)
        else:
            carriage = setup.carriage_table(record.carriage.ways, record.carriage.area_imbalance)
            area_map = setup.area_map(carriage)
        self.record = record
        self.area_map = area_map
        number_area_markets(record.memory, area_map)
        self.carriage = carriage
        self.watched_tiles: Tuple[str, ...] = ()   # tiles whose market books are kept beside the port's and the capital's; not saved
        self._own_hectares: Dict[str, float] = {}   # land households' own plots took this year, by tile
        self._year_plot_options: Optional[Dict[str, list]] = None   # own_plot_options, built once for the year being run
        self.years_stepped = 0   # years `step` has begun in this process; a reader that keeps a figure of the record until the next year compares it. Never saved
        self._work_hours: Dict[str, float] = {}     # household work each cohort keeps back this year; set when the year plans it
        self._year_arrays: Optional[YearArrays] = None   # the year arrays as the last phase left them: the next year starts from them (`YearArrays.carried`), the equity is built over them. Never saved

    def change_setup(self, **changes: Any) -> None:
        """The one place the setup changes: a new setup with these fields replaced (the old one is never edited in place)."""
        self.setup = dataclasses.replace(self.setup, **changes)
        note_written()      # what readers of the memory (the wage rule's trades and opening wages) took from the old setup is read again

    def set_improvements(self, improvements: Mapping[str, Mapping[str, Any]]) -> bool:
        """Rebuild the carriage table over these built ways, partition the market areas again over it and
        carry the markets' memory to the new areas; False when they are the ways it already has."""
        if dict(improvements) == self.record.carriage.ways:
            return False
        self.record.carriage.set_ways({key: dict(way) for key, way in improvements.items()})
        return self._rebuild_carriage()

    def _rebuild_carriage(self) -> bool:
        """Carriage over the current ways and return trips, the market areas partitioned again over it, the
        markets' memory carried to the new areas."""
        self.carriage = self.setup.carriage_table(self.record.carriage.ways, self.record.carriage.area_imbalance)
        area_map = self.setup.area_map(self.carriage)
        follow(self.record, self.area_map, area_map)
        number_area_markets(self.record.memory, area_map)
        self.area_map = area_map
        return True

    def rebuild_market_areas(self) -> None:
        """Partition the market areas again over the setup's goods (goods the setup gained are new markets)."""
        self._rebuild_carriage()

    def follow_flows(self) -> bool:
        """Price the carriage by last year's flows: where the opposite flow fills more of the carriers'
        return trips, a tonne costs less. False when the (stepped) emptiness of the returns is unchanged."""
        imbalance = flow_imbalance(self.record.carriage)
        if imbalance == self.record.carriage.area_imbalance:
            return False
        self.record.carriage.set_area_imbalance(imbalance)
        return self._rebuild_carriage()

    def view(self) -> YearView:
        return CreditView(self.record.memory, self.record.book, self.area_map, self.setup.currency_id, self.setup,
                          labour_area, loans=lambda: self.record.credit.loans, equity=self._equity_read,
                          loss_rates=lambda: self.record.credit.loss_rates,
                          pooled=self.record.credit.contracts.deposit_value)

    def _equity_read(self, view) -> Dict[str, float]:
        arrays = self._year_arrays
        if arrays is not None and not (arrays.area_map is self.area_map and same_source(arrays.source, source_of(self.setup))):
            arrays = None      # built for another setup or area map: read the producers one by one
        return equity.holdings(self.setup, self.record, view, arrays)

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

    def step(self, inputs: EconomyYearInputs) -> YearOutcome:
        self.years_stepped += 1
        with collection_paused():
            try:
                return self._run_year(inputs)
            finally:
                self._year_plot_options = None

    def _run_year(self, inputs: EconomyYearInputs) -> YearOutcome:
        changes: Dict[str, Any] = {}
        if inputs.tax_rates:
            changes["tax_forms"] = taxes.with_rates(self.setup.tax_forms, inputs.tax_rates)
        if inputs.site_limits:   # empty keeps the last declared
            changes["site_limits"] = tuple(inputs.site_limits)
        if changes:
            self.change_setup(**changes)
        setup, record = self.setup, self.record
        self._year_plot_options = own_production_options(setup.recipes, setup.land_per_run, setup.basket)
        record.sort_in_saved_order()
        self.follow_flows()
        self.carriage.set_scale(carriage_hours.wage_scale(setup, record, self.carriage))   # the carriers' labour at the year's wage
        record.book.start_year()
        stocks_at_start = stocks_held(record.book)
        ledger = YearLedger(import_accounts=frozenset(inputs.import_accounts), export_accounts=frozenset(inputs.export_accounts),
                             state_capacity=inputs.state_capacity, book=record.book, markets=record.memory.tables)
        self._follow_population(inputs)
        self._follow_yields(inputs)
        sites.apply_site_limits(record, setup)
        view = self.view()
        arrays = self._year_arrays = YearArrays.carried(self._year_arrays, setup, record, self.area_map, view)
        money = setup.currency_id
        debt_relief.forgive(record, inputs.debt_relief_tiles)
        titles_moves.apply(record, inputs.title_moves)
        tax_farming.run_auctions(setup, record, inputs.farmed_forms, record.memory.rates[setup.currency_id])
        lending.lend_working_capital(setup, record, view)
        plans = plan_year.plans_of(setup, record, view, arrays, money)
        labour_bids = LabourBidTable()
        plans.write_labour_bids(labour_bids)
        for orders in inputs.engine_orders.values():
            labour_bids.add_objects(orders.labour_bids)
        state_budget.plan_year(setup, record, view, labour_bids)
        staff_mint(setup, record, view, labour_bids)
        carriage_hours.write_bids(labour_bids, setup, record)    # merchants' carriers, from last year's shipments
        outside_option = outside_option_by_tile(setup, record, view)
        land_lease_year.lease_in_market(setup, record, view, self.own_plot_options())
        land_bid_year.take_up_own(setup, record, self.own_plot_options())
        levied_tiles = tuple(inputs.population_by_tile)      # the tiles of the nation whose state levies (port_levy.py spreads the hours over them)
        everyone = labour_offer_rows(setup, record, view, outside_option, inputs.labour_levy_hours_per_worker, levied_tiles,
                                     LabourOfferRows(labour_bids.trades, labour_bids.areas))
        for orders in inputs.engine_orders.values():
            everyone.add_objects(orders.labour_offers)    # a seat's own hours, sold at the market's wage
        context = labour_context(setup, record, view, self.carriage, inputs, self.own_plot_options(), outside_option)
        held_placed = bondage_hours.place_held(
            record.unfree.bonded_held, lambda area, trade: people_by_trade(record.labour.workforce, area).get(trade, 0.0), everyone, labour_bids,
            setup.working_hours_per_year, context.ask_floor_per_worker_year, labour_area)
        keep = bondage_hours.payable_keep(held_placed.keep, lambda employer: record.book.balance(employer, money))
        bondage_keep.post_keep(record.book, ledger, keep, money)
        context = dataclasses.replace(context, outlay_room=outlay_room.by_plan_table(     # after the keep is paid out of the purses
            plans, setup.state_agent, record.state_budget, lambda employer: record.book.balance(employer, money),
            record.book.balances_of(plans.ids, money)))
        placed = bondage_hours.place(record.unfree.bondage, held_placed.offers, held_placed.bids,
                                     bondage_hours.works_of_producers(record), bondage.BONDED_HOURS_OWED_SHARE)
        everyone, labour_bids = placed.offers, placed.bids
        supply = self._hour_supply(everyone, view)
        people_before = flight_step.people_before(record.labour)
        labour_report = clear_labour(setup, record, labour_bids, everyone, ledger, context, supply=supply)
        flight_step.settle(setup, record, inputs, labour_report, people_before, context, self.carriage)
        ledger.migrated_by_tile = {area_tile(area): change for area, change in sorted(labour_report.migrated.items()) if change}
        state_budget.lapse_unspent_wages(record.state_budget, state_budget.wages_paid(ledger.labour_results, setup.state_agent))
        offers, kept = supply.sold, supply.kept
        _bought, _paid, ledger.bonded_lots, bought_held = bonded_purchase.settle(
            record.book, money, labour_report.bonded_lots)
        bondage_hours.hold(record.unfree.bonded_held, bought_held)
        bondage_hours.deliver(ledger.hours_hired, placed)
        bondage_hours.deliver(ledger.hours_hired, held_placed)
        record.labour.set_hours_paid_by_employer(dict(sorted(ledger.hours_hired.as_plain().items())))   # what seats' staff books read; one pass over the ledger table
        capital_year.insure(setup, record, view, inputs.harvest_factor, view.year, inputs.institutions)     # cover is bought and the weather settles it
        self._grow_own(offers, ledger, inputs.harvest_factor, kept)
        capital_year.note_exposure(setup, record, view, self.area_map, ledger, inputs.harvest_factor, inputs.institutions)
        order_book = new_order_book(setup, record)
        funds = cohort_orders(setup, record, view, ledger, order_book, self.own_plot_options())
        state_orders(setup, record, view, self.area_map, order_book, {})
        mint_held = mint_orders(setup, record, self.area_map, order_book,
                                ledger.hours_hired.get(mint_agent(setup), {}))
        engine = OrderRows(order_book, ENGINE)
        for agent, orders in sorted(inputs.engine_orders.items()):
            engine.bids_from(orders.bids)
            engine.offers_from(orders.offers)
        engine.write()
        plan_table.write_bids(plans, order_book)
        land_bid_year.write_firm_land_bids(setup, record, view, plans.wanted_runs_by_id(), plans.budget_total_by_id(), order_book)
        funds = capital_year.before_lending(setup, record, view, ledger, funds, view.year, inputs.institutions)   # holders sell shares and loans; depositors run on banks
        funds, pledged = banks.intermediate(setup, record, funds, view.year, inputs.institutions)
        kept = capital_year.snapshot(record, money, funds)
        plant_runs = self._lend(funds, view, order_book, ledger, pledged, inputs.credit_asks)
        capital_year.invest_idle(setup, record, view, funds, kept, inputs.institutions)       # savings neither lent nor put in shares go into a fund
        merchant_orders(setup, record, view, self.area_map, self.carriage, order_book)
        for producer_id, runs in self._rebuild_worn_plant(view, order_book).items():
            plant_runs[producer_id] = plant_runs.get(producer_id, 0.0) + runs
        clear_goods(setup, record, view, self.area_map, order_book, plans, ledger, self.watched_tiles, arrays)
        land_bid_year.take_up_bought(setup, record)
        settle_mint(record, mint_held, ledger)
        close_mint_year(setup, record)
        rent = land_market.settle_year(setup, record, view,
                                       plans.wanted_runs_by_id(), self._own_hectares, inputs.land_tax_share_of_rent,
                                       lambda: land_lease_year.asks(setup, record, view, self.own_plot_options()), ledger,
                                       land_lease_year.own_plot_returns(setup, record, view, self.own_plot_options()))
        interest = self._service_loans(view.year)
        bonded = bondage.service(record, money, ledger.wages_in, placed.value_placed, placed.cash_share)
        record.book.transfer_many(bonded)
        ledger.note_paid_outside_markets(bonded)
        for payee, amount in list(zip(keep.cohorts, keep.amounts.tolist())) + [(payment.payee, payment.amount) for payment in bonded]:
            interest[payee] = interest.get(payee, 0.0) + amount
        titles_inheritance.divide_estates(record)
        dispatch_merchants(setup, record, self.carriage, ledger, self.area_map)
        money_taxes(setup, record, view, ledger)
        self._build_plant(plant_runs)
        close_view = self.view()
        received = dict(interest)
        for payment in rent:
            received[payment.payee] = received.get(payment.payee, 0.0) + payment.amount
        arrays = self._year_arrays = close_agents(setup, record, close_view, ledger, self.area_map, self.carriage, arrays, received)
        arrays = self._year_arrays = arrays.sync(setup, record, close_view)      # the memory is read once for entry and the restake
        open_entrants(setup, record, close_view, self.area_map, ledger.unmet_demand, self.carriage,
                      standing_block(ledger, inputs.standing_bids), arrays)
        restake_owners(setup, record, close_view, arrays)
        extraction = sites.extraction_by_tile(record, setup)
        close_idle_producers(setup, record)
        wear_and_spoilage(setup, record, inputs.durable_users)
        level = remember_basket_price_level(setup, record)
        record.memory.advance_year()
        return self._outcome(ledger, level, extraction, stocks_at_start)

    # ---- the year's pieces ------------------------------------------------------------------
    def _follow_population(self, inputs: EconomyYearInputs) -> None:
        """Demography's people and working-age people per tile are the one count: each tile's cohorts are rescaled to its
        people, and their working people to its working-age people (the working-age share follows demography); then the
        labour core's workers and trainees on each tile to the working people the cohorts hold. The core adds no entrants or leavers
        of its own."""
        if not inputs.population_by_tile:
            return
        record = self.record
        cohort_people.follow_population(record.cohorts, inputs.population_by_tile, inputs.working_people_by_tile)
        store = record.cohorts
        working = cohort_people.total_by_tile(store, "working_people").tolist()
        names = store.names["tiles"].name_list
        for tile, people in sorted((names[number], working[number]) for number in np.unique(store.tile_numbers()).tolist()):
            area = labour_area(tile)
            held = people_in(record.labour.workforce, area)
            if held <= 0.0:      # the core holds nobody there: the tile's working people start as the unskilled trade
                record.labour.add_workers(area, self.setup.unskilled_trade, people)
            elif held != people:
                scale_people(record.labour.workforce, area, people / held)

    def _follow_yields(self, inputs: EconomyYearInputs) -> None:
        producer_table.set_column(self.record.producers, "yield_factor", inputs.yield_factor_by_producer, inputs.yield_factor_by_producer.values())

    def own_plot_options(self):
        """The recipes a household can grow its need from itself; built once for a year being run."""
        if self._year_plot_options is not None:
            return self._year_plot_options
        setup = self.setup
        return own_production_options(setup.recipes, setup.land_per_run, setup.basket)

    def _fixed_home_hours(self, everyone, view) -> Tuple[Dict[str, float], Dict[str, float]]:
        """(own-plot plan hours, household work hours) each cohort keeps back whatever the wage: the plan at the tile's
        usual fertility (it plants before it knows the harvest), and the household work it does itself
        (household_work_year.py)."""
        plan, held, options = {}, self.hectares_held(), self.own_plot_options()
        for cohort_id, cohort in sorted(self.record.cohorts.items()):
            tile = self.setup.tiles.get(cohort.tile)
            plan[cohort_id] = hours_for_own_plan(cohort, options, tile.fertility if tile else 0.0,
                                                 self.setup.recipes, self.setup.land_per_run, held.get(cohort_id, 0.0))
        self._work_hours = household_offers_year.decide(self.setup, self.record, view, everyone)
        return plan, self._work_hours

    def _hour_supply(self, everyone, view) -> HourSupply:
        """The hours households sell as a schedule against the wage (labour_supply.py)."""
        plan, work = self._fixed_home_hours(everyone, view)
        plot = household_offers_year.plot_parameters_by_cohort(self.setup, self.record, view, everyone, self.own_plot_options(),
                                                              self.hectares_held())
        faced = everyone.faced_wages(view.wage, trade_wages.faced_wage)
        return HourSupply(everyone, plan, work, {}, faced, plot_parameters=plot)

    def hectares_held(self) -> Dict[str, float]:
        return titles_plots.hectares_held(self.setup, self.record)

    def _grow_own(self, offers, ledger: YearLedger, harvest_factor: float = 1.0,
                  kept: Optional[Dict[str, float]] = None) -> None:
        """Hours kept back and hours nobody hired go into the household's own plot (households_own.py)."""
        setup, record = self.setup, self.record
        options = self.own_plot_options()
        kept = kept or {}
        self._own_hectares = {}
        held = self.hectares_held()
        offered = sold_hours_by_worker(offers)
        grown_steps = []       # a cohort's grown goods are one batch; the batches are posted together, in cohort order
        for cohort_id, cohort in sorted(record.cohorts.items()):
            idle = (offered.get(cohort_id, 0.0) + kept.get(cohort_id, 0.0) - ledger.hours_sold.get(cohort_id, 0.0)
                    - min(kept.get(cohort_id, 0.0), self._work_hours.get(cohort_id, 0.0)))   # household work is not spare hours
            tile = setup.tiles.get(cohort.tile)
            hours_used: Dict[str, float] = {}
            moves, grown, units = own_production(cohort, idle, options, setup.recipes,
                                                 (tile.fertility if tile else 0.0) * harvest_factor,
                                                 setup.basket_for(cohort.tile), setup.land_per_run,
                                                 held.get(cohort.agent_id, 0.0), hours_used)
            if hours_used:
                ledger.own_plot_hours[cohort_id] = hours_used
            ledger.spare_hours[cohort_id] = max(0.0, idle - sum(hours_used.values()))
            if moves:
                grown_steps.append(((), moves))
                ledger.grown[cohort_id] = grown
                ledger.grown_units[cohort_id] = units
                hectares = plot_hectares(units, options, setup.recipes, setup.land_per_run,
                                         (tile.fertility if tile else 0.0) * harvest_factor)
                self._own_hectares[cohort.tile] = self._own_hectares.get(cohort.tile, 0.0) + hectares
        post_in_order(record.book, grown_steps)

    def _service_loans(self, year: int) -> Dict[str, float]:
        """Payments due at the year's end, out of the year's sales: before carriage, taxes and the owners'
        dividends, since a lender is paid ahead of them."""
        return lending.service(self.record, self.setup.currency_id, year, self.setup.debt_bondage_years)

    def _lend(self, funds, view, order_book, ledger, pledged=None, credit_asks=()) -> Dict[str, float]:
        """New loans from savings. A producer that borrowed to build bids for its plant goods, a household
        for its floors; a merchant's cargo is bought from its enlarged cash (merchant_orders follows)."""
        record, setup = self.record, self.setup
        money = setup.currency_id
        priced_by_tile: Dict[str, list] = {}
        requests = record.credit.take_requests()
        requests = (requests + list(credit_asks) + lending.household_requests(setup, record, view, ledger, priced_by_tile)
                    + lending.merchant_requests(setup, record, view, self.area_map, self.carriage))
        record.credit.open_lending(funds, money)
        if not requests:
            record.credit.clear_expansion()      # a working-capital loan struck ahead of the year left no plant to wait for
            if funds:       # savings on offer and nobody borrowing
                record.memory.set_rate(money, credit_idle_rate.rate_with_no_borrowers(record.memory.rates.get(money), funds))
            return {}
        debt = credit_claims.principal_by_borrower(record.credit.loans)
        offered = credit_lines.hold_reserve(funds, record.capital_markets.banks)     # the reserve is held out of every lender's offer
        clearing = credit.clear_with_cause(requests, offered, money, record.memory.rates.get(money), debt,
                                           credit_claims.arrears_history(record.credit.loans, record.credit.remembered_defaults),
                                           year=view.year,
                                           rate_ceiling=capital_market.RATE_CEILING_SHARE * setup.opening_rate,
                                           expected_inflation=lending.expected_inflation_of(record))
        loans, unmet = clearing.loans, clearing.unmet
        every_loan = loans
        loans, granted = credit_lines.split_lines(loans, [ask.borrower for ask in credit_asks])
        record.credit.grant_lines(granted, [ask.borrower for ask in credit_asks])
        banks.draw_deposits(record, loans, pledged or {}, view.year, money)       # a bank takes its depositors' funds for the loans it makes
        transfer_rows.post_payments(record.book, *credit.disbursement_rows(loans))
        record.credit.add_loans(loans)
        for loan in every_loan:
            record.credit.note_lent(loan)
        if clearing.cause is None and clearing.rate is not None:
            record.memory.set_rate(money, clearing.rate)      # a year in which nothing cleared leaves the last cleared rate
        rate = record.memory.rates[money]       # the opening sets one
        # a plant request lenders left unmet is offered to the savers as shares (the money they raise is plant like a loan's)
        raised = shares.raise_equity(record, money, unmet, funds, every_loan, rate, shares.rate_floor_of(setup),
                                    record.capital_markets.capital.share_buy_orders)
        merchants_credit.stake(record.merchants, {loan.borrower: loan.principal for loan in loans})
        lending.bid_household_loans(setup, record, view, ledger, loans, order_book, priced_by_tile)

        def plant_worth_of(request):
            recipe_id = record.producers.recipe_id_of(request.borrower)
            if recipe_id is None:
                return None
            return plant_worth_ratio(request.maximum_rate, rate, setup.recipes[recipe_id].plant_life_years)

        asked, worth = lend_requests.asked_and_worth(requests, plant_worth_of)
        plant_runs: Dict[str, float] = {}
        for borrower, principal in [(loan.borrower, loan.principal) for loan in loans] + sorted(raised.items()):
            producer = record.producers.get(borrower)
            runs = record.credit.expansion_runs.get(borrower, 0.0)
            if producer is None or runs <= 0.0 or not asked.get(borrower):
                continue
            funded_runs = runs * min(1.0, principal / asked[borrower])
            plant_runs[borrower] = plant_runs.get(borrower, 0.0) + funded_runs
            # no dearer than the price at which the new plant would earn just the loan's rate
            self._bid_for_plant(producer, funded_runs, principal, worth.get(borrower, 1.0), view, order_book)
        record.credit.clear_expansion()
        return plant_runs

    def _rebuild_worn_plant(self, view, order_book) -> Dict[str, float]:
        """Producers that covered their costs bid, from their own cash, for the plant goods that rebuild
        what wore out last year, no dearer than the price at which the plant still earns the live rate."""
        record, setup = self.record, self.setup
        money = setup.currency_id
        rate = max(own_rate(view, money), 1e-9)
        rebuilt: Dict[str, float] = {}
        worn = record.credit.take_rebuilds()
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
            if earning is None or not earning > rate or cash <= 0.0:
                continue
            self._bid_for_plant(producer, runs, cash, plant_worth_ratio(earning, rate, recipe.plant_life_years),
                                view, order_book)
            rebuilt[producer_id] = runs
        return rebuilt

    def _bid_for_plant(self, producer, runs, budget, worth_ratio, view, order_book) -> None:
        recipe = self.setup.recipes[producer.recipe_id]
        rows = OrderRows(order_book, LOAN)
        for good, per_run in sorted(recipe.plant_goods.items()):
            if good not in self.area_map.goods():
                continue
            area = view.area_of(good, producer.tile)
            price = view.price(good, area)
            if not price:
                continue
            rows.bid(producer.agent_id, good, area, producer.tile, per_run * runs, 0.0, price, 0.0, budget,
                     maximum_price=price * max(1.0, worth_ratio))
        rows.write()

    def _build_plant(self, plant_runs: Dict[str, float]) -> None:
        """Plant goods a producer received are built in; capacity grows by the share that arrived."""
        record, setup = self.record, self.setup
        built_steps = []       # each producer's plant goods are one batch; none reads another's stock, so they are posted together
        for producer_id, runs in sorted(plant_runs.items()):
            store = record.producers
            row = store.row_of.get(producer_id)
            if row is None:
                continue
            tile = store.names["tiles"].name_list[store.table.tile[row]]
            recipe = setup.recipes[store.names["recipes"].name_list[store.table.recipe[row]]]
            share = 1.0
            for good, per_run in recipe.plant_goods.items():
                wanted = per_run * runs
                if wanted > 0.0:
                    share = min(share, record.book.stock(producer_id, good, tile) / wanted)
            # only the goods the capacity actually built uses are consumed; the rest stays in stock
            built_steps.append(((), [GoodsMove(producer_id, EDGE_CONSUMPTION, good, tile, per_run * runs * share, "built into plant")
                                     for good, per_run in sorted(recipe.plant_goods.items()) if per_run * runs * share > 0.0]))
            producer_table.set_fields(store, producer_id, capacity_runs=max(0.0, store.value(row, "capacity_runs") + runs * share))
        post_in_order(record.book, built_steps)

    def _outcome(self, ledger: YearLedger, level: float, extraction, stocks_at_start) -> YearOutcome:
        record, setup = self.record, self.setup
        money = setup.currency_id
        hired, idle = hours_totals(ledger.labour_results)
        mean_wages = national_wages(record)
        hunger = cohort_people.hunger_by_tile(record.cohorts, self.setup.hunger_need)
        output: Dict[str, float] = {}
        for (_agent, good), quantity in ledger.output.items():
            output[good] = output.get(good, 0.0) + quantity
        record.goods.reset_output()
        for (agent, good), quantity in sorted(ledger.output.items()):
            tile = record.producers.tile_of(agent)
            if tile is not None and quantity > 0.0:
                record.goods.add_output(tile, good, quantity)
        prices = national_prices(record)
        return YearOutcome(year=record.memory.year, basket_price_level=level, prices=prices,
                           wages=mean_wages, rate=record.memory.rates[money],
                           money_supply=record.book.money_supply(money), hunger_by_tile=hunger,
                           output=dict(sorted(output.items())), idle_hours=idle, hired_hours=hired,
                           wage_floor_per_hour=ledger.wage_floor_per_hour, extraction=extraction,
                           money_audit=year_report(record),
                           migrated_by_tile=dict(ledger.migrated_by_tile), bonded_lots=list(ledger.bonded_lots),
                           accounts=build_accounts(setup, record, ledger, stocks_at_start, prices, mean_wages))
