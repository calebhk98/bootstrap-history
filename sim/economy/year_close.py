"""The year's end: carriage, money taxes, the mint, every agent's close, spoilage, and what the
markets remember for next year."""
import math
from types import MappingProxyType
from typing import Dict, Mapping, Tuple

from . import producer_table
from .staffed_runs import staffed_runs
from .expected_sales import demand_seen, market_capacities
from . import (practice, firm_finance, firm_year, tax_farming, merchants_transit, carriage_hours, carriage_wear, currency, expansion_price, households, inventory, merchants, metal_stock, ownership, producer_exit, shares,
               producers, producers_close, state_budget, tariffs, taxes, trade_wages)
from .home_scope import has_partners, home_cohorts, on_home_tile
from .household_work_year import cohort_basket
from . import households_cohort
from .market_memory import market_key
from .national_prices import national_prices, traded_spending_weights, usual_volumes
from .notional import recently_traded_goods
from .setup import labour_area
from .taxes_bases import YearFacts
from .types import is_edge
from .inventory import held_stock
from .year_ledger import YearLedger
from .replaced import replaced
from .producers import live_input_prices, live_wages
from .rates import own_rate


def foreign_agents(setup, record) -> set:
    """Agents living or working on another country's tiles: the home state does not assess them."""
    if not has_partners(setup):
        return set()
    away = lambda tile: not on_home_tile(setup, tile, True)   # noqa: E731
    return ({cohort.agent_id for cohort in record.cohorts.values() if away(cohort.tile)}
            | {producer.agent_id for producer in record.producers.values() if away(producer.tile)}
            | {merchant.agent_id for merchant in record.merchants.values() if away(merchant.home_tile)})


def tax_facts(setup, record, view, ledger: YearLedger) -> YearFacts:
    money = setup.currency_id
    hours = setup.working_hours_per_year
    away = foreign_agents(setup, record)
    home = home_cohorts(setup, record)
    working = {cohort.agent_id: cohort.working_people for cohort in home}
    wage_year = {cohort.agent_id: trade_wages.wage_in_view(setup, view, setup.unskilled_trade, labour_area(cohort.tile)) * hours
                 for cohort in home}
    cash = {agent: record.book.balance(agent, money) for agent in record.book.agents()
            if not is_edge(agent) and agent not in away}
    taxpayers = frozenset((set(record.cohorts) | set(record.producers) | set(record.merchants)) - set(away))
    return YearFacts(currency=money, working_people=working, wage_per_labour_year=wage_year, cash=cash, taxpayers=taxpayers,
                     imports_paid={key: paid for key, paid in ledger.imports_paid.items() if key[0] not in away},
                     exports_received={key: paid for key, paid in ledger.exports_received.items() if key[0] not in away})


def money_taxes(setup, record, view, ledger: YearLedger) -> None:
    forms = [form for form in setup.tax_forms if not form.paid_in]
    received = 0.0
    carried_duty = tariffs.carried_duty_transfers(ledger.carried_in, setup.carried_tariff,
                                                  lambda carrier: record.book.balance(carrier, setup.currency_id),
                                                  setup.state_agent, setup.currency_id)
    if carried_duty:     # the economy's own merchants bringing goods in from another country of it
        record.book.transfer_many(carried_duty)
        received += math.fsum(transfer.amount for transfer in carried_duty)
    farmed = dict(record.taxes.tax_farms)
    received += math.fsum(farm["price"] for farm in farmed.values())      # the farmers paid up front
    if forms:
        facts = tax_facts(setup, record, view, ledger)
        owed_to_state = [form for form in forms if form.name not in farmed]
        cash_left = dict(facts.cash)       # shared by every assess call below: a payer liable to two forms pays from one purse
        transfers, _moves, assessments = taxes.assess(owed_to_state, facts, setup.state_agent, {}, ledger.state_capacity,
                                                       setup.hiding, cash_left)
        for form in forms:
            if form.name in farmed:
                farmed_transfers, _farmed_moves, farmed_assessments = taxes.assess(
                    [form], facts, farmed[form.name]["farmer"], {}, tax_farming.TAX_FARMER_REACH, setup.hiding, cash_left,
                    frozenset({setup.state_agent}))      # the state does not pay a farmer for its own treasury
                record.book.transfer_many(farmed_transfers)
                ledger.note_postings(farmed_transfers)
                assessments = assessments + farmed_assessments
        record.book.transfer_many(transfers)
        ledger.note_postings(transfers)
        received += math.fsum(transfer.amount for transfer in transfers)
        tax_farming.remember_year(record.taxes, assessments, tuple(farmed), ledger.state_capacity)
    record.taxes.lapse_farms()
    state_budget.close_year(setup, record, ledger, received)


def wear_and_spoilage(setup, record, durable_users=()) -> None:
    book = record.book
    holdings: Dict[Tuple[str, str, str], float] = {}
    for agent in book.agents():
        if is_edge(agent):
            continue
        for good, tiles in book.holdings(agent)["goods"].items():
            for tile, quantity in tiles.items():
                if quantity > 0.0:
                    holdings[(agent, good, tile)] = quantity
    book.move_many(inventory.spoilage_moves(holdings, setup.specs))
    fleets = {carriage_wear.account(merchant_id) for merchant_id in record.merchants}     # carriers age in the merchants' fleets
    book.move_many(inventory.wear_moves(holdings, setup.specs, set(record.cohorts) | set(durable_users) | fleets))
    cash = {agent: book.balance(agent, record.currency.currency_id) for agent in book.agents() if not is_edge(agent)}
    book.transfer_many(metal_stock.yearly_wear(cash, record.currency))


def close_agents(setup, record, view, ledger: YearLedger, area_map, carriage,
                 income_received: Mapping[str, float] = MappingProxyType({})) -> None:
    """Close every agent's year. `income_received` is the year's other property income by payee (interest, rent); it is
    added to the dividends and profits paid out here, so the households close on this year's property income and it is
    what the record keeps."""
    money = setup.currency_id
    property_income: Dict[str, float] = dict(income_received)
    traded, round_prices = ledger.market_totals()
    clearing_prices = {key: price for key, price in round_prices.items() if traded[key] > 0.0 and price is not None}
    prepared_buyers: Dict = {}
    service_lives = {good: spec.service_life_years for good, spec in setup.specs.items()}
    cohorts_by_tile: Dict = {}           # the tiles' cohorts, unchanged until the households close below
    loans_of: Dict[str, list] = {}
    for loan in record.credit.loans:
        loans_of.setdefault(loan.borrower, []).append(loan)
    crews_of_recipe: Dict[str, list] = {}
    for each in record.producers.values():
        crews_of_recipe.setdefault(each.recipe_id, []).append(each.crew_runs)
    live_prices: Dict[Tuple[str, str], tuple] = {}
    pool_by_recipe_trade: Dict[Tuple[str, str], float] = {}     # the crews' practice is read before the loop, so one pool per recipe and trade

    def pooled(recipe_id: str, trade: str) -> float:
        if (recipe_id, trade) not in pool_by_recipe_trade:
            pool_by_recipe_trade[(recipe_id, trade)] = practice.pool_units(crews_of_recipe[recipe_id], trade)
        return pool_by_recipe_trade[(recipe_id, trade)]
    market_capacity = market_capacities(((each.tile, setup.recipes[each.recipe_id].outputs, each.capacity_runs * each.yield_factor)
                                         for each in record.producers.values() if each.idle_years <= 0), area_map.area_of)
    for producer_id, producer in sorted(record.producers.items()):
        recipe = setup.recipes[producer.recipe_id]
        if producer.idle_years > 0:      # bankrupt: idle, no dividend (Eurace@Unibi, Firm_bankruptcy_idle_counter)
            producer_table.put_producer(record.producers, replaced(producer, idle_years=producer.idle_years - 1))
            shares.note_dividend(record.capital_markets, producer_id, ())
            continue
        revenue = ledger.sales_in.get(producer_id, 0.0)
        costs = ledger.running_costs(producer_id)
        prices_here = _prices_here(clearing_prices, recipe, area_map.area_of, producer.tile)
        worked = worked_runs(producer, recipe, ledger, producers.paying_output(recipe, prices_here))
        price_share = expansion_price.price_share_of(ledger.bids_by_market, traded, area_map.area_of, producer.tile,
                                                   prepared_buyers)
        demand_runs = runs_sold(producer, recipe, ledger, record.book, area_map.area_of, prices_here, market_capacity)
        if (producer.recipe_id, producer.tile) not in live_prices:     # last year's prices do not change inside the close
            live_prices[(producer.recipe_id, producer.tile)] = (live_input_prices(producer, recipe, view), live_wages(producer, recipe, view))
        inputs, wages = live_prices[(producer.recipe_id, producer.tile)]
        closed = producers_close.close_year(producer, recipe, revenue, costs, view, worked, price_share,
                                            [good for good in recipe.outputs if good in setup.specs and not setup.specs[good].portable],
                                            service_lives, firm_finance.interest_due(loans_of.get(producer_id, []), producer_id),
                                            demand_runs,
                                            spoilage={good: setup.specs[good].spoilage_per_year for good in recipe.outputs if good in setup.specs},
                                            inputs=inputs, wages=wages)
        year = None
        if not closed.exited:       # the dividend, the financing check and bankruptcy follow Eurace@Unibi (firm_year.py)
            closed, _paid, year = firm_year.settle_year(setup, record, view, producer, closed, recipe, revenue, costs,
                                                        loans_of.get(producer_id, []), inputs, wages)
        shares.note_dividend(record.capital_markets, producer_id, closed.transfers)
        if year is not None and year.write_off_ratio > 0.0:
            firm_year.write_off(record, producer_id, year.write_off_ratio)
        if closed.exited:
            paid = producer_exit.exit_producer(record, producer_id, list(closed.transfers))
            for transfer in paid:
                property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
            continue
        paid = ownership.spread(record, closed.transfers, cohorts_by_tile)
        record.book.transfer_many(paid)
        worn = producer.capacity_runs - closed.producer.capacity_runs
        if worn > 0.0:
            ledger.plant_worn[producer_id] = worn
        if closed.replacement_runs > 0.0 and revenue > costs:
            record.credit.plan_rebuild(producer_id, closed.replacement_runs)     # covering its costs, it rebuilds the wear its plan needs
        for transfer in paid:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
        if closed.loan_request is not None:
            record.credit.ask_for_loan(closed.loan_request)
            record.credit.plan_expansion(producer_id, closed.expansion_runs)
        producer_table.put_producer(record.producers, _with_practice(
            _with_sales(closed.producer, recipe, ledger, demand_runs, prices_here), producer.last_runs,
            {trade: pooled(producer.recipe_id, trade) for trade in producer.crew_runs}))
    prices, volumes = learned_prices(ledger.market_totals(), record.memory)
    anchors = {(good, area.area_id): area.anchor_tile for good in area_map.goods() for area in area_map.areas(good)}
    ordered = (sorted(prices.items()), sorted(volumes.items()))
    interest_rate = own_rate(view, money)
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        transfers = merchants.close_year(merchant, prices, volumes, record.book.balance(merchant.agent_id, money),
                                         held_stock(record.book, merchant.agent_id), area_map.area_of, money,
                                         interest_rate, ordered,
                                         _news_lag_of(carriage, merchant.home_tile, anchors))
        paid = ownership.spread(record, transfers, cohorts_by_tile)
        record.book.transfer_many(paid)
        for transfer in paid:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
    if carriage_hours.hires(setup):    # after the owners took their profit: the cash left is what next year's carriers can be paid from
        record.credit.ask_for_loans(carriage_hours.wage_loans(setup, record, ledger.crew_hours_bought,
                                                           {(result.trade, result.area): result.hours_hired + result.idle_hours
                                                            for result in ledger.labour_results}))
    for lender, interest in record.capital_markets.take_pool_income().items():     # the actors' pool paid this year
        property_income[lender] = property_income.get(lender, 0.0) + interest
    offered_prices: Dict = {}      # the prices households are closed on do not change while they close
    for cohort_id, cohort in sorted(record.cohorts.items()):
        received = dict(ledger.received.get(cohort_id, {}))
        for good, quantity in ledger.grown.get(cohort_id, {}).items():
            received[good] = received.get(good, 0.0) + quantity
        income = ledger.wages_in.get(cohort_id, 0.0) + property_income.get(cohort_id, 0.0)
        spent = ledger.money_out.get(cohort_id, 0.0)
        closed, moves = households.close_year(cohort, received, view, setup.specs, cohort_basket(setup, record, cohort, buying=False),
                                                   income, spent, offered_prices)
        record.book.move_many(held_only(moves, record.book))
        households_cohort.put_cohort(record.cohorts, closed)
    record.capital_markets.set_property_income(property_income)


def _news_lag_of(carriage, home, anchors):
    """`lag_years` for a merchant at `home`: the news lag to a market's anchor tile, worked out once per tile."""
    lag_at_tile: Dict = {}

    def lag_years(good, area):
        tile = anchors.get((good, area))
        if tile is None:
            return None
        lag = lag_at_tile.get(tile)
        if lag is None:
            lag = lag_at_tile[tile] = merchants_transit.news_lag(carriage, home, tile)
        return lag
    return lag_years


def learned_prices(totals, memory):
    """(prices, volumes) by (good, area) that traders learn from the year, from its `(quantity, price)` market totals:
    the price the market now remembers, which for a market that sold nothing is what buyers would have paid."""
    volumes, cleared = totals
    prices = {}
    for key, price in cleared.items():
        remembered = memory.prices.get(market_key(*key), price)
        if remembered is not None:      # a market with no price remembered and none quoted has none to learn from
            prices[key] = remembered
    return prices, volumes


def held_only(moves, book):
    """The moves with each giver's quantity cut to what it holds: settlement can deliver a rounding hair
    less than a fill, and an agent consumes what it has, not what its fills say."""
    return [move if is_edge(move.giver) else
            replaced(move, quantity=min(move.quantity, max(0.0, book.stock(move.giver, move.good, move.tile))))
            for move in moves]


def _with_practice(producer, runs_last_year, pool):
    """The crew's practice after the year's runs (practice.py); growth in runs is hired hands."""
    if not producer.crew_runs:
        return producer
    return replaced(producer, crew_runs=practice.crew_runs_after_year(
        producer.crew_runs, max(0.0, producer.last_runs) / max(1.0, producer.workshops),
        practice.hired_share(runs_last_year, producer.last_runs), pool))


def _prices_here(clearing_prices, recipe, area_of, tile) -> Dict[str, float]:
    """The year's clearing price of each output of `recipe` in the market of `tile`; an output that did not trade is absent."""
    here = {}
    for good in recipe.outputs:
        price = clearing_prices.get((good, area_of(good, tile)))
        if price is not None:
            here[good] = price
    return here


def worked_runs(producer, recipe, ledger: YearLedger, paying) -> float:
    """Runs the producer worked this year: the output of its paying good over what a run makes of it (the recipe's
    quantity times the yield); none when the plant yields nothing."""
    per_run = recipe.outputs[paying] * producer.yield_factor
    return ledger.output.get((producer.agent_id, paying), 0.0) / per_run if per_run > 0.0 else 0.0


def runs_sold(producer, recipe, ledger: YearLedger, book, area_of, prices, market_capacity=None) -> float:
    """Runs of the recipe whose outputs it sold this year: the value sold of all outputs at the year's `prices` over
    the value of one run's outputs, so an output nobody buys (straw, manure) neither counts nor drags the figure down.
    An output sells its quantity plus its share of the unmet demand in its market. With no output priced, the output
    that sold most of its run stands for the run. A plant that yields nothing learns nothing: its expectation stands."""
    if producer.yield_factor <= 0.0:
        return producer.expected_sales
    made = {good: per_run * producer.yield_factor for good, per_run in recipe.outputs.items()}     # units a run yields
    seen = {}
    for good in recipe.outputs:
        market = (good, area_of(good, producer.tile))
        seen[good] = demand_seen(ledger.sold.get((producer.agent_id, good), 0.0), book.stock(producer.agent_id, good, producer.tile),
                                 made[good] * producer.capacity_runs, (market_capacity or {}).get(market, 0.0),
                                 ledger.unmet_demand.get(market, 0.0))
    priced = [good for good in made if prices.get(good) is not None]    # an output with no price carries no weight
    value_of_run = math.fsum(made[good] * prices[good] for good in priced)
    if value_of_run > 0.0:
        return math.fsum(seen[good] * prices[good] for good in priced) / value_of_run
    return max(seen[good] / made[good] for good in made)


def _with_sales(producer, recipe, ledger: YearLedger, sold: float, prices):
    """Expected sales move toward the runs it sold this year (`sold`, from `runs_sold`)."""
    worked = worked_runs(producer, recipe, ledger, producers.paying_output(recipe, prices))
    staffed = staffed_runs(recipe.labour_hours, ledger.hours_hired.get(producer.agent_id, {}))
    staffed = None if staffed is None else min(staffed, producer.capacity_runs)
    if producer.expected_sales <= 0.0:
        return replaced(producer, expected_sales=sold, last_runs=worked, staffed_runs=staffed)
    share = producers.EXPECTATION_ADJUSTMENT_SHARE
    return replaced(producer, expected_sales=producer.expected_sales + share * (sold - producer.expected_sales),
                               last_runs=worked, staffed_runs=staffed)


def remember_basket_price_level(setup, record) -> float:
    """The fixed basket's cost at today's prices over its cost at the base prices, over the goods that
    traded recently (notional.RECENT_TRADE_YEARS): a good that has not cleared holds only an estimate,
    and an estimate frozen at its base price would damp measured inflation. The basket's quantities
    stay those of the opening; which goods are priced follows trade."""
    recent = recently_traded_goods(record.memory)
    prices = {good: price for good, price in national_prices(record).items() if good in recent}
    base = record.goods.index_base_prices or setup.opening_prices
    level = currency.basket_price_level(prices, base, record.goods.opening_basket)
    # the median's weights are what the goods traded for last year; the opening basket's value stands in until they trade
    spending = traded_spending_weights(usual_volumes(record),
                                       record.memory.last_year_prices or prices, set(record.goods.opening_basket)) \
        or {good: quantity * base[good] for good, quantity in record.goods.opening_basket.items() if good in base}
    record.memory.note_basket_price_level(
        setup.currency_id, level, currency.price_inflation(prices, record.memory.last_year_prices, spending))
    record.memory.set_last_year_prices(prices)
    return level


def rebase_basket_price_level(setup, record) -> None:
    """Today's prices become the index base (level one) and the last level the market's memory and each household
    compare against becomes one, so the rebase is not read as a jump in prices. Expected inflation is a yearly
    rate, the same in any base, so it is carried over unchanged."""
    money = setup.currency_id
    record.goods.set_index_base_prices(national_prices(record))
    record.memory.rebase_price_levels(money)
    households_cohort.rebase_price_level(record.cohorts)


