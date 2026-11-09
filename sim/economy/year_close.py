"""The year's end: carriage, money taxes, the mint, every agent's close, spoilage, and what the
markets remember for next year."""
import math
from types import MappingProxyType
from typing import Dict, Mapping, Tuple

from . import producer_table
from .staffed_runs import staffed_runs
from .expected_sales import demand_seen, market_capacities
from . import (practice, firm_finance, firm_year, tax_farming, merchants_news, carriage_hours, currency, expansion_price, merchants, ownership, producer_exit, shares,
               producers, producers_close, state_budget, tariffs, taxes, trade_wages)
from .cohort_store import table_of
from .home_scope import has_partners, home_cohort_ids, on_home_tile
from . import households_cohort
from .market_memory import market_key
from .national_prices import national_prices, traded_spending_weights, usual_volumes
from .notional import recently_traded_goods
from .setup import labour_area
from .taxes_bases import YearFacts
from .types import is_edge
from .inventory import held_stock
from .year_ledger import YearLedger
from .year_arrays import YearArrays
from .year_close_households import close_households
from .year_close_producers import close_producers_of_year
from .wear_year import wear_and_spoilage      # noqa: F401  (the economy imports it from here)
from .replaced import replaced
from .producers import live_input_prices, live_wages
from .rates import own_rate


def foreign_agents(setup, record) -> set:
    """Agents living or working on another country's tiles: the home state does not assess them."""
    if not has_partners(setup):
        return set()
    away = lambda tile: not on_home_tile(setup, tile, True)   # noqa: E731
    return (set(table_of(record.cohorts).ids_on_tiles(away))
            | set(record.producers.ids_on_tiles(away))
            | {merchant.agent_id for merchant in record.merchants.values() if away(merchant.home_tile)})


def tax_facts(setup, record, view, ledger: YearLedger) -> YearFacts:
    money = setup.currency_id
    hours = setup.working_hours_per_year
    away = foreign_agents(setup, record)
    home = home_cohort_ids(setup, record)
    store = table_of(record.cohorts)
    rows = store.rows_of(home)
    working = dict(zip(home, store.floats("working_people", rows)))
    wage_of_tile: Dict[str, float] = {}
    wage_year = {}
    for agent, tile in zip(home, store.tile_names(rows)):
        if tile not in wage_of_tile:
            wage_of_tile[tile] = trade_wages.wage_in_view(setup, view, setup.unskilled_trade, labour_area(tile)) * hours
        wage_year[agent] = wage_of_tile[tile]
    holders = [agent for agent in record.book.agents() if not is_edge(agent) and agent not in away]
    cash = dict(zip(holders, record.book.balances_of(holders, money).tolist()))      # one block read, in the book's name order
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


def close_agents(setup, record, view, ledger: YearLedger, area_map, carriage, arrays,
                 income_received: Mapping[str, float] = MappingProxyType({})) -> YearArrays:
    """Close every agent's year. `income_received` is the year's other property income by payee (interest, rent); it is
    added to the dividends and profits paid out here, so the households close on this year's property income and it is
    what the record keeps. Returns the year arrays as the close leaves them."""
    money = setup.currency_id
    property_income: Dict[str, float] = dict(income_received)
    cohorts_by_tile: Dict = {}           # the tiles' cohorts, unchanged until the households close below
    crews_of_recipe: Dict[str, list] = record.producers.crews_by_recipe(in_id_order=False)
    pool_by_recipe_trade: Dict[Tuple[str, str], float] = {}     # the crews' practice is read before the loop, so one pool per recipe and trade

    def pooled(recipe_id: str, trade: str) -> float:
        if (recipe_id, trade) not in pool_by_recipe_trade:
            pool_by_recipe_trade[(recipe_id, trade)] = practice.pool_units(crews_of_recipe[recipe_id], trade)
        return pool_by_recipe_trade[(recipe_id, trade)]
    arrays = close_producers_of_year(setup, record, view, ledger, arrays, property_income, pooled)
    prices, volumes = learned_prices(ledger.market_totals(), record.memory)
    anchors = {(good, area.area_id): area.anchor_tile for good in area_map.goods() for area in area_map.areas(good)}
    news = merchants_news.YearNews(prices, volumes, anchors)
    interest_rate = own_rate(view, money)
    merchants.learn_year(record.memory.tables, news, carriage)
    for transfer in merchants.close_all(record.memory.tables, record.book, area_map, money, interest_rate):
        paid = ownership.spread(record, (transfer,), cohorts_by_tile)
        record.book.transfer_many(paid)
        for payment in paid:
            property_income[payment.payee] = property_income.get(payment.payee, 0.0) + payment.amount
    if carriage_hours.hires(setup):    # after the owners took their profit: the cash left is what next year's carriers can be paid from
        record.credit.ask_for_loans(carriage_hours.wage_loans(setup, record, ledger.crew_hours_bought,
                                                           {(result.trade, result.area): result.hours_hired + result.idle_hours
                                                            for result in ledger.labour_results}))
    for lender, interest in record.capital_markets.take_pool_income().items():     # the actors' pool paid this year
        property_income[lender] = property_income.get(lender, 0.0) + interest
    close_households(setup, record, view, ledger, property_income)
    record.capital_markets.set_property_income(property_income)
    return arrays


def learned_prices(totals, memory):
    """(prices, volumes) by (good, area) that traders learn from the year, from its `(quantity, price)` market totals:
    the price the market now remembers, which for a market that sold nothing is what buyers would have paid."""
    volumes, cleared = totals
    prices = {}
    keys = list(cleared)
    for key, quoted, remembered in zip(keys, cleared.values(), memory.prices.get_many([market_key(*key) for key in keys], None)):
        if remembered is None:
            remembered = quoted
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


