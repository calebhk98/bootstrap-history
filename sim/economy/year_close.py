"""The year's end: carriage, money taxes, the mint, every agent's close, spoilage, and what the
markets remember for next year."""
import math
from typing import Dict, Tuple

from sim.geography.api import flow_ledger
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from .expected_sales import demand_seen
from . import (practice, firm_year, carried_book, carriage_fleet_book, tax_farming, merchants_transit, carriage_hours, carriage_wear, currency, expansion_price, households, inventory, merchants, metal_stock, ownership, producer_exit, shares,
               producers, producers_close, state_budget, tariffs, taxes)
from .household_work_year import basket_key, cohort_basket
from .households_cohort import renewed
from .market_memory import market_key
from .national_prices import national_prices, traded_spending_weights
from .notional import recently_traded_goods
from .setup import labour_area
from .taxes_bases import YearFacts
from .types import is_edge
from .year_goods import _held_stock
from .year_ledger import YearLedger
from .replaced import replaced


def dispatch_merchants(setup, record, carriage, ledger: YearLedger, area_map) -> None:
    """Merchants carry what they bought. The crew hours the shipments need were hired in the year's labour
    market (carriage_hours.bids) and limit what is carried; a merchant with no plan yet (it has not shipped)
    is not limited. A fee is paid in parts to those who supply them: the crew by the labour market, the carriers
    worn and the feed the animals eat by the merchant buying them in the goods market (carriage_wear), and
    what is left (the carriers' interest, their losses, the margin) stays with the merchant that owns the carriers,
    whose owner draws it as profit. Where the setup names no carriers the whole fee still goes to the poorest
    households of the tile the goods leave (Complaints/552)."""
    money = setup.currency_id
    crew = carriage_hours.crew_for(setup, record, carriage)
    index = carriage_hours.hired_index(ledger) if crew is not None else {}
    carriers = {}
    for cohort in record.cohorts.values():
        held = carriers.get(cohort.tile)
        if held is None or cohort.income_class < record.cohorts[held].income_class:
            carriers[cohort.tile] = cohort.agent_id
    carried: dict = {}
    carried_goods: dict = {}
    carrier_goods = carriage_wear.carrier_goods(setup)
    prices = carriage_wear.last_prices(setup, record) if carrier_goods else {}
    wear = carriage_wear.Wear(setup, carriage, record.area_imbalance) if carriage_wear.wears(setup) else None
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        record.book.move_many(merchants_transit.advance(merchant, setup.specs))    # hauls on the road for years reach the tile or spoil
    lives = carriage_fleet_book.fleet_lives(setup) if wear is not None else {}
    own_capacity, hired, lent = {}, {}, {}
    if lives:     # a merchant carries no more than its fleet bears; idle fleets are hired out to those short of one
        for merchant in record.merchants.values():
            carriage_fleet_book.keep(merchant, record.book, carrier_goods)
            own_capacity[merchant.agent_id] = carriage_fleet_book.own_capacity(record.book, merchant.agent_id, lives)
        needed = {merchant.agent_id: carriage_fleet_book.wear_needed(
            merchant, _held_stock(record.book, merchant.agent_id), setup.specs, wear, lives) for merchant in record.merchants.values()}
        hired, lent = carriage_fleet_book.share_idle(own_capacity, needed)
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        fills = ledger.buy_fills.get(merchant.agent_id, [])
        if not fills:
            if crew is not None:
                merchant.carriage_hours_wanted = {}     # nothing shipped: no carriers to bid for next year
                merchant.carriage_money_wanted = {}
            if wear is not None:     # its fleet's wanted size stands: it may ship again
                merchant.carrier_wear, merchant.carrier_team_days = {}, {}
                carriage_wear.settle(merchant, record.book, carrier_goods, {})
            continue
        hire = None
        if crew is not None:
            if carriage_hours.planned(merchant):
                ledger.crew_hours_bought[merchant.agent_id] = {
                    (trade, area): bought for (employer, trade, area), (bought, _paid) in index.items()
                    if employer == merchant.agent_id}
            hours_hired, wages = ((carriage_hours.engaged(record, merchant, index)) if carriage_hours.planned(merchant)
                                  else (None, {}))
            hire = merchants.CrewHire(crew.hours_per_tonne, hours_hired, wages,
                                    lambda key: carriage_hours.last_wage(record, key), area_map.area_of)
        done = merchants.dispatch(merchant, fills, carriage, setup.specs, money,
                                  record.book.balance(merchant.agent_id, money), _held_stock(record.book, merchant.agent_id),
                                  carrier_of=carriers.get, crew=hire,
                                  carrier_money=None if wear is None else (
                                      lambda source, destination, each=merchant: carriage_wear.money_per_tonne(
                                          prices, wear, source, destination)),
                                  margin_kept=wear is not None,
                                  fleet=carriage_fleet_book.limit_for(wear, own_capacity[merchant.agent_id], hired.get(merchant.agent_id, {}))
                                  if lives else None)
        record.book.post(done.transfers, done.moves)
        ledger.note_postings(done.transfers, "wages")
        if crew is not None:
            merchant.carriage_hours_wanted = done.crew_hours_wanted
            merchant.carriage_money_wanted = done.crew_money_wanted
        if wear is not None:
            merchant.carrier_wear, merchant.carrier_team_days = carriage_wear.exposure(wear, done.moves, setup.specs)
            carriage_wear.settle(merchant, record.book, carrier_goods,
                                 {good: units for good, units in merchant.carrier_wear.items() if good not in lives})
            if lives:
                merchant.carrier_fleet_wanted = {good: max(0.0, units - hired.get(merchant.agent_id, {}).get(good, 0.0))
                                                 for good, units in done.fleet_wanted.items()}
                rent = carriage_fleet_book.rent_transfers(
                    merchant.agent_id, hired.get(merchant.agent_id, {}), merchant.carrier_wear,
                    own_capacity[merchant.agent_id], lent, prices, money, record.book.balance(merchant.agent_id, money))
                record.book.transfer_many(rent)
                ledger.note_postings(rent)
        for move in done.moves:
            tonnes = move.quantity * setup.specs[move.good].unit_mass_kg / KILOGRAMS_PER_TONNE
            flow_ledger.record_flow(carried, move.tile, move.receiver_tile, tonnes)
            carried_book.note_carried(carried_goods, move.good, move.tile, move.receiver_tile, move.quantity, tonnes,
                                      _price_on(record, area_map, move.good, move.tile),
                                      _price_on(record, area_map, move.good, move.receiver_tile))
    record.carried = carried
    record.carried_goods = carried_goods


def _price_on(record, area_map, good, tile):
    """The price the good's market area holding the tile last cleared at; None when it has no market there or
    none has cleared."""
    try:
        return record.memory.prices.get(market_key(good, area_map.area_of(good, tile)))
    except KeyError:
        return None


def foreign_agents(setup, record) -> set:
    """Agents living or working on another country's tiles: the home state does not assess them."""
    if len(setup.countries()) < 2:
        return set()
    away = lambda tile: setup.country_of(tile) != setup.civ_id   # noqa: E731
    return ({cohort.agent_id for cohort in record.cohorts.values() if away(cohort.tile)}
            | {producer.agent_id for producer in record.producers.values() if away(producer.tile)}
            | {merchant.agent_id for merchant in record.merchants.values() if away(merchant.home_tile)})


def tax_facts(setup, record, view, ledger: YearLedger) -> YearFacts:
    money = setup.currency_id
    hours = setup.working_hours_per_year
    away = foreign_agents(setup, record)
    home_cohorts = [cohort for cohort in record.cohorts.values() if cohort.agent_id not in away]
    working = {cohort.agent_id: cohort.working_people for cohort in home_cohorts}
    wage_year = {cohort.agent_id: (view.wage(setup.unskilled_trade, labour_area(cohort.tile)) or 0.0) * hours
                 for cohort in home_cohorts}
    cash = {agent: record.book.balance(agent, money) for agent in record.book.agents()
            if not is_edge(agent) and agent not in away}
    return YearFacts(currency=money, working_people=working, wage_per_labour_year=wage_year, cash=cash,
                     imports_paid={key: paid for key, paid in ledger.imports_paid.items() if key[0] not in away},
                     exports_received={key: paid for key, paid in ledger.exports_received.items() if key[0] not in away})


def money_taxes(setup, record, view, ledger: YearLedger) -> None:
    forms = [form for form in setup.tax_forms if not form.paid_in]
    received = 0.0
    duty = tariffs.duty_transfers(setup.import_duty_share, ledger.border_imports_paid, setup.state_agent, setup.currency_id)
    if duty:
        record.book.transfer_many(duty)
        received += math.fsum(transfer.amount for transfer in duty)
    farmed = dict(record.tax_farms)
    received += math.fsum(farm["price"] for farm in farmed.values())      # the farmers paid up front
    if forms:
        facts = tax_facts(setup, record, view, ledger)
        owed_to_state = [form for form in forms if form.name not in farmed]
        transfers, _moves, assessments = taxes.assess(owed_to_state, facts, setup.state_agent, {}, setup.state_capacity,
                                                       setup.hiding)
        for form in forms:
            if form.name in farmed:
                farmed_transfers, _farmed_moves, farmed_assessments = taxes.assess(
                    [form], facts, farmed[form.name]["farmer"], {}, tax_farming.TAX_FARMER_REACH, setup.hiding)
                record.book.transfer_many(farmed_transfers)
                ledger.note_postings(farmed_transfers)
                assessments = assessments + farmed_assessments
        record.book.transfer_many(transfers)
        ledger.note_postings(transfers)
        received += math.fsum(transfer.amount for transfer in transfers)
        tax_farming.remember_year(record, assessments, tuple(farmed), setup.state_capacity)
    record.tax_farms = {}
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


def close_agents(setup, record, view, ledger: YearLedger, area_map, carriage) -> None:
    money = setup.currency_id
    property_income: Dict[str, float] = {}
    traded = {(result.good, result.area): result.quantity for result in ledger.clearings}
    clearing_prices = {(result.good, result.area): result.price for result in ledger.clearings if result.quantity > 0.0}
    prepared_buyers: Dict = {}
    service_lives = {good: spec.service_life_years for good, spec in setup.specs.items()}
    cohorts_by_tile: Dict = {}           # the tiles' cohorts, unchanged until the households close below
    loans_of: Dict[str, list] = {}
    for loan in record.loans:
        loans_of.setdefault(loan.borrower, []).append(loan)
    crews_of_recipe: Dict[str, list] = {}
    for each in record.producers.values():
        crews_of_recipe.setdefault(each.recipe_id, []).append(each.crew_runs)
    for producer_id, producer in sorted(record.producers.items()):
        recipe = setup.recipes[producer.recipe_id]
        if producer.idle_years > 0:      # bankrupt: idle, no dividend (Eurace@Unibi, Firm_bankruptcy_idle_counter)
            record.producers[producer_id] = replaced(producer, idle_years=producer.idle_years - 1)
            shares.note_dividend(record, producer_id, ())
            continue
        revenue = ledger.sales_in.get(producer_id, 0.0)
        costs = ledger.running_costs(producer_id)
        paying = producers.paying_output(recipe, _prices_here(clearing_prices, recipe, area_map.area_of, producer.tile))
        per_run = recipe.outputs[paying]
        worked = ledger.output.get((producer_id, paying), 0.0) / (per_run * producer.yield_factor or per_run)
        price_share = expansion_price.price_share_of(ledger.bids_by_market, traded, area_map.area_of, producer.tile,
                                                   prepared_buyers)
        closed = producers_close.close_year(producer, recipe, revenue, costs, view, worked, price_share,
                                            [good for good in recipe.outputs if good in setup.specs and not setup.specs[good].portable],
                                            service_lives)
        year = None
        if not closed.exited:       # the dividend, the financing check and bankruptcy follow Eurace@Unibi (firm_year.py)
            closed, _paid, year = firm_year.settle_year(setup, record, view, producer, closed, recipe, revenue, costs,
                                                        loans_of.get(producer_id, []))
        shares.note_dividend(record, producer_id, closed.transfers)
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
            record.worn_runs[producer_id] = closed.replacement_runs     # covering its costs, it rebuilds the wear its plan needs
        for transfer in paid:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
        if closed.loan_request is not None:
            record.loan_requests.append(closed.loan_request)
            record.expansion_runs[producer_id] = closed.expansion_runs
        record.producers[producer_id] = _with_practice(
            _with_sales(closed.producer, recipe, ledger, record.book, area_map.area_of, traded, clearing_prices), producer.last_runs,
            {trade: practice.pool_units(crews_of_recipe[producer.recipe_id], trade) for trade in producer.crew_runs})
    prices, volumes = learned_prices(ledger.clearings, record.memory)
    anchors = {(good, area.area_id): area.anchor_tile for good in area_map.goods() for area in area_map.areas(good)}
    ordered = (sorted(prices.items()), sorted(volumes.items()))
    interest_rate = view.interest_rate(money)
    for merchant in sorted(record.merchants.values(), key=lambda each: each.agent_id):
        transfers = merchants.close_year(merchant, prices, volumes, record.book.balance(merchant.agent_id, money),
                                         _held_stock(record.book, merchant.agent_id), area_map.area_of, money,
                                         interest_rate, ordered,
                                         _news_lag_of(carriage, merchant.home_tile, anchors))
        paid = ownership.spread(record, transfers, cohorts_by_tile)
        record.book.transfer_many(paid)
        for transfer in paid:
            property_income[transfer.payee] = property_income.get(transfer.payee, 0.0) + transfer.amount
    if carriage_hours.hires(setup):    # after the owners took their profit: the cash left is what next year's carriers can be paid from
        record.loan_requests.extend(carriage_hours.wage_loans(setup, record, ledger.crew_hours_bought,
                                                           {(result.trade, result.area): result.hours_hired + result.idle_hours
                                                            for result in ledger.labour_results}))
    for cohort_id, cohort in sorted(record.cohorts.items()):
        received = dict(ledger.received.get(cohort_id, {}))
        for good, quantity in ledger.grown.get(cohort_id, {}).items():
            received[good] = received.get(good, 0.0) + quantity
        income = ledger.wages_in.get(cohort_id, 0.0) + record.property_income.get(cohort_id, 0.0)
        spent = ledger.money_out.get(cohort_id, 0.0)
        closed, moves = households.close_year(cohort, received, view, setup.specs, cohort_basket(setup, record, cohort, buying=False),
                                                   income, spent)
        record.book.move_many(held_only(moves, record.book))
        record.cohorts[cohort_id] = closed
    record.property_income = property_income


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


def learned_prices(clearings, memory):
    """(prices, volumes) by (good, area) that traders learn from the year: the price the market now
    remembers, which for a market that sold nothing is what buyers would have paid."""
    prices, volumes = {}, {}
    for result in clearings:
        key = (result.good, result.area)
        prices[key] = memory.prices.get(market_key(result.good, result.area), result.price)
        volumes[key] = result.quantity
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


def runs_sold(producer, recipe, ledger: YearLedger, book, area_of, traded, prices) -> float:
    """Runs of the recipe whose outputs it sold this year: the value sold of all outputs at the year's `prices` over
    the value of one run's outputs, so an output nobody buys (straw, manure) neither counts nor drags the figure down.
    An output sells its quantity plus its share of the unmet demand in its market (`traded`: quantity sold by (good,
    area)). With no output priced, the output that sold most of its run stands for the run."""
    seen = {}
    for good, per_run in recipe.outputs.items():
        market = (good, area_of(good, producer.tile))
        seen[good] = demand_seen(ledger.sold.get((producer.agent_id, good), 0.0), book.stock(producer.agent_id, good, producer.tile),
                                 traded.get(market, 0.0), ledger.unmet_demand.get(market, 0.0))
    value_of_run = math.fsum(per_run * prices.get(good, 0.0) for good, per_run in recipe.outputs.items())
    if value_of_run > 0.0:
        return math.fsum(seen[good] * prices.get(good, 0.0) for good in recipe.outputs) / value_of_run
    return max(seen[good] / per_run for good, per_run in recipe.outputs.items())


def _with_sales(producer, recipe, ledger: YearLedger, book, area_of, traded, clearing_prices=None):
    """Expected sales move toward the runs it sold this year (`runs_sold`), measured by value over all its outputs."""
    prices = _prices_here(clearing_prices or {}, recipe, area_of, producer.tile)
    sold = runs_sold(producer, recipe, ledger, book, area_of, traded, prices)
    paying = producers.paying_output(recipe, prices)
    per_run = recipe.outputs[paying]
    worked = ledger.output.get((producer.agent_id, paying), 0.0) / (per_run * producer.yield_factor or per_run)
    if producer.expected_sales <= 0.0:
        return replaced(producer, expected_sales=sold, last_runs=worked)
    share = producers.EXPECTATION_ADJUSTMENT_SHARE
    return replaced(producer, expected_sales=producer.expected_sales + share * (sold - producer.expected_sales),
                               last_runs=worked)


def remember_basket_price_level(setup, record) -> float:
    """The fixed basket's cost at today's prices over its cost at the base prices, over the goods that
    traded recently (notional.RECENT_TRADE_YEARS): a good that has not cleared holds only an estimate,
    and an estimate frozen at its base price would damp measured inflation. The basket's quantities
    stay those of the opening; which goods are priced follows trade."""
    recent = recently_traded_goods(record.memory)
    prices = {good: price for good, price in national_prices(record).items() if good in recent}
    base = record.index_base_prices or setup.opening_prices
    level = currency.basket_price_level(prices, base, record.opening_basket)
    # the median's weights are what the goods traded for last year; the opening basket's value stands in until they trade
    spending = traded_spending_weights(record.memory.volume_weights or record.volumes,
                                       record.memory.last_year_prices or prices, set(record.opening_basket)) \
        or {good: quantity * base.get(good, 0.0) for good, quantity in record.opening_basket.items()}
    record.memory.note_basket_price_level(
        setup.currency_id, level, currency.price_inflation(prices, record.memory.last_year_prices, spending))
    record.memory.last_year_prices = dict(prices)
    return level


def rebase_basket_price_level(setup, record) -> None:
    """Today's prices become the index base (level one) and the last level the market's memory and each household
    compare against becomes one, so the rebase is not read as a jump in prices. Expected inflation is a yearly
    rate, the same in any base, so it is carried over unchanged."""
    money = setup.currency_id
    record.index_base_prices = national_prices(record)
    record.memory.basket_price_levels[money] = 1.0
    record.memory.price_levels[money] = 1.0
    record.cohorts = {agent: renewed(cohort, last_basket_price_level=1.0)
                      for agent, cohort in record.cohorts.items()}


def check_money(record) -> float:
    """Largest residual share across currencies and goods: zero when everything has a counterparty."""
    report = record.book.check_conservation(1e-9)
    shares = list(report.money.values()) + list(report.goods.values())
    return max((abs(share) for share in shares), default=0.0) if shares else 0.0
