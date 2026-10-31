"""The only door into sim/economy/: what code outside the package may import.

Outside code imports from here and reaches the simulation's economy through an `Economy` (built by
the markets module's port, sim/markets/port*.py), never through a submodule or a private name. The accessors below read the
record's internals so that callers do not hold `economy.record.<field>` in their own code.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the markets module's port hands it what it needs (sim/markets/port*.py)

import math

from . import carried_book, carriage_wear, crop_sites, unit_cost, country_figures, diagnostics, late_recipes, opening_metal, household_grinding, households, households_work, labour_state, land_rents, market_curves, prices_at as tile_prices, taxes, tile_costs, workforce_settle, workforce_version
from .bank_founding import found_from_outside
from .diagnostics import person_equivalent_unemployment
from .fixture_setups import GRAIN as FIXTURE_STAPLE, LABOURER as FIXTURE_UNSKILLED_TRADE, small_setup as fixture_small_setup, stationary_setup as fixture_stationary_setup
from .banks import DEPOSIT_BANKING
from .funds import POOLED_FUNDS
from .insurance import INSURANCE_UNDERWRITING, RISK_POOLING
from .secondary_trade import BOND_MARKET, SHARE_TRADING
from .credit_lines import line_request as credit_line_request
from .currency import currency_from_coin_standard
from .economy import Economy
from .foreign import external_orders
from .market_memory import market_key
from .opening_rate import against_history, opening_market_rate, solved_opening_rate
from .metal_stock import COIN_WEAR_PER_YEAR
from .notional import shown_prices, shown_prices_with_kinds
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .protocols import AgentOrders, YearInputs
from .recipes import recipes_from_production_data
from . import plant_builds
from .tool_wear import with_tool_wear
from .record import EconomyRecord
from .setup import EconomySetup, TradeSpec, goods_specs, recipe_tile_key
from .types import (EDGE_CARGO, EDGE_CONSUMPTION, EDGE_EXCHANGE, EDGE_EXTERNAL, EDGE_LEGACY, EDGE_MINT, EDGE_PRODUCTION, EDGE_WEAR, Bid,
                    GoodsMove, Offer, SiteLimit, Transfer, external_edge)
from .year_accounts import YearAccounts
from . import baseline_checks, settling, spin_up_sensitivity
from .unit_cost import variable_cost_per_run
from .titles_value import title_wealth
from .debt_relief import indebted_tiles as record_indebted_tiles
from .titles_moves import holdings as record_title_holdings
from .spin_up_state import spin_up_state as year_spin_up_state
from .year_close import rebase_basket_price_level
from .year_labour import trade_premium
from sim.world import capital_market

__all__ = [
    "FIXTURE_STAPLE", "FIXTURE_UNSKILLED_TRADE", "fixture_small_setup", "fixture_stationary_setup",
    "YearAccounts", "baseline_checks", "settling", "spin_up_sensitivity",
    "carriage_wear", "crop_sites", "unit_cost", "diagnostics", "household_grinding", "households", "households_work", "taxes", "tile_costs", "currency_from_coin_standard", "Economy", "external_orders",
    "price_response", "prices_at", "offered_units", "watch_tiles",
    "shown_prices", "Producer", "expected_output_prices", "live_input_prices", "live_wages", "AgentOrders",
    "YearInputs", "recipe_tile_key", "recipes_from_production_data", "plant_builds", "with_tool_wear", "EconomyRecord", "EconomySetup", "TradeSpec", "SiteLimit",
    "goods_specs", "EDGE_EXTERNAL", "EDGE_LEGACY", "EDGE_CARGO", "EDGE_CONSUMPTION", "EDGE_PRODUCTION", "EDGE_EXCHANGE", "external_edge", "Bid", "GoodsMove", "Offer", "Transfer",
    "variable_cost_per_run", "rebase_basket_price_level", "trade_premium", "title_wealth",
    "traded_volumes", "country_traded_volumes", "country_opening_basket", "market_record", "opening_quantities", "opening_prices_in_hours", "wages_by_trade", "wages_by_trade_weighted", "interest_rate", "producers_of",
    "external_trade_net", "external_trade_volume", "account_balance", "account_holdings",
    "credit_room", "credit_line_request", "economy_from_record", "blank_economy", "export_record", "economy_book", "economy_contracts", "finish_spin_up", "note_spin_up_result", "spin_up_state", "money_year_figures","shown_prices_of","shown_price_kinds_of",
    "settle_agent_takings", "indebted_tiles", "fugitive_share_by_tile", "title_holdings", "money_revenue_forms", "admit_recipes", "move_goods", "post_transfers", "cohort_incomes", "cohort_land_rents", "land_rent_per_hectare",
    "land_rent_paid_by_tile", "land_rent_at_tile", "DEPOSIT_BANKING", "POOLED_FUNDS", "INSURANCE_UNDERWRITING", "RISK_POOLING", "BOND_MARKET", "SHARE_TRADING", "country_figures", "carried_book", "idle_hours_by_trade", "output_by_tile",
    "person_equivalent_unemployment", "labour_market_rows",
]

_KEY_SEPARATOR = "|"


def found_bank_from_outside(economy, founder, capital_units, year, edge):
    """A bank founded by an actor whose money the engine keeps: `capital_units` come in over `edge` to its account and into
    the bank. The bank, or None when the capital is not positive."""
    return found_from_outside(economy.record, economy.setup.currency_id, founder, capital_units, year, edge)


def traded_volumes(economy):
    """Last year's traded quantity of each good, summed over its markets."""
    totals = {}
    for key, volume in economy.record.volumes.items():
        good = key.split(_KEY_SEPARATOR, 1)[0]
        totals[good] = totals.get(good, 0.0) + volume
    return totals


def country_traded_volumes(economy, country=None):
    """Last year's traded quantity of each good over the markets of `country` (the home country when none is named)."""
    return country_figures.traded_volumes(economy, country or economy.setup.civ_id)


def country_opening_basket(economy, country=None):
    """Quantity of each good in the opening basket that falls to `country` (the home country when none is named)."""
    return country_figures.opening_basket(economy, country or economy.setup.civ_id)


def market_record(economy, good):
    """What the markets of one good did last year, summed over its areas, in the good's units: `sold` (traded),
    `unsold` (what sellers would have sold at the year's price and did not) and `unmet` (what buyers wanted at
    it beyond what was sold)."""
    record = economy.record
    totals = {"sold": 0.0, "unsold": 0.0, "unmet": 0.0}
    for name, figures in (("sold", record.volumes), ("unsold", record.unsold), ("unmet", record.unmet)):
        for key, quantity in figures.items():
            if key.split(_KEY_SEPARATOR, 1)[0] == good:
                totals[name] += quantity
    return totals


def opening_quantities(economy):
    """Quantity of each good in the opening basket."""
    return dict(economy.record.opening_basket)


def opening_prices_in_hours(economy):
    """Opening price of each good in hours of the unskilled trade's opening wage: the weights a basket is valued at."""
    wage = economy.setup.opening_wages.get(economy.setup.unskilled_trade, 0.0)
    if not wage > 0.0:
        return {}
    return {good: price / wage for good, price in sorted(economy.setup.opening_prices.items()) if price > 0.0}


def people_by_trade(economy, country=None):
    """Working people by trade across the labour areas of `country` (the home country when the economy holds
    several and none is named; every area when it holds one), as the labour core's state holds them."""
    def sum_people():
        scope = country_figures.home_when_shared(economy, country)
        if scope is None:
            return labour_state.people_by_trade_everywhere(economy.record.workforce)
        return country_figures.people_by_trade(economy, scope)
    return workforce_version.cached(economy.record.workforce, ("people_by_trade", country), sum_people)


def people_by_tile_and_trade(economy):
    """Working people of the labour core by tile and trade, over every labour area (trainees are not counted)."""
    return {labour_state.area_tile(area): labour_state.people_by_trade(economy.record.workforce, area)
            for area in sorted(economy.record.workforce.workers)}


def wages_by_trade(economy):
    """Last year's wages per hour, as a list of market wages for each trade."""
    rows = {}
    for key, wage in economy.record.memory.wages.items():
        rows.setdefault(key.split(_KEY_SEPARATOR, 1)[0], []).append(wage)
    return rows


def land_rent_per_hectare(economy, country=None):
    """Mean rent per hectare-year producers paid last year over the tiles of `country` where land was let
    (the home country's when the economy holds several; zero where none was)."""
    scope = country_figures.home_when_shared(economy, country)
    tiles = country_figures.country_tiles(economy, scope)
    rents = [rent for tile, rent in economy.record.land_rent.items() if rent > 0.0 and tile in tiles]
    return sum(rents) / len(rents) if rents else 0.0


def land_rent_at_tile(economy, tile, country=None):
    """Rent per hectare-year the land market let land at on one tile last year; the mean over the tiles of `country`
    (the home country's when none is named) where land was let where none was let on this tile (zero where none was let
    anywhere)."""
    rent = economy.record.land_rent.get(tile, 0.0)
    return rent if rent > 0.0 else land_rent_per_hectare(economy, country)


def output_by_tile(economy):
    """What the producers made last year, tile -> good -> units, as a sorted copy."""
    return {tile: dict(sorted(row.items())) for tile, row in sorted(economy.record.output_by_tile.items())}


def land_rent_paid_by_tile(economy):
    """Rent producers paid on each tile where land was let last year, in the economy's units."""
    return land_rents.rent_paid_by_tile(economy.setup, economy.record)


def idle_hours_by_trade(economy, country=None):
    """(hours offered and not hired, hours offered) of each trade in the labour markets of `country` (the home
    country's when the economy holds several) in the last clearing: the jobs the labour core did not find."""
    return country_figures.idle_hours_by_trade(economy, country_figures.home_when_shared(economy, country))


def labour_market_rows(economy):
    """(people, hours offered, hours hired) of each (trade, area) labour market in the last clearing, in key order, for
    `person_equivalent_unemployment`. Offered is hired plus idle; the plot trade (people working their own land) is
    left out."""
    record = economy.record
    plot = labour_state.plot_trade(economy.setup)
    rows = []
    for key in sorted(record.hours_idle):
        trade, area = key.split(_KEY_SEPARATOR, 1)
        if trade == plot:
            continue
        people = math.fsum(record.workforce.workers.get(area, {}).get(trade, ()))
        hired = record.hours_hired.get(key, 0.0)
        rows.append((people, hired + record.hours_idle[key], hired))
    return rows


def wages_by_trade_weighted(economy, country=None):
    """Last year's wage per hour of each trade: the remembered wage of each of its labour markets weighted
    by the hours hired there last year. A trade that hired no hours is left out (its remembered wages are
    opening seeds, not clearings), except the unskilled trade, whose wage prices the rest. Of `country`'s
    markets (the home country's when the economy holds several)."""
    scope = country_figures.home_when_shared(economy, country)
    if scope is not None:
        wages = country_figures.wages_per_hour(economy, scope)
    else:
        rows = {}
        for key, wage in economy.record.memory.wages.items():
            rows.setdefault(key.split(_KEY_SEPARATOR, 1)[0], []).append((wage, economy.record.hours_hired.get(key, 0.0)))
        wages = {trade: (sum(wage * hours for wage, hours in pairs) / sum(hours for _wage, hours in pairs)
                         if sum(hours for _wage, hours in pairs) > 0.0 else sum(wage for wage, _hours in pairs) / len(pairs))
                 for trade, pairs in rows.items()}
    idle_and_offered = country_figures.idle_hours_by_trade(economy, scope)
    unskilled = economy.setup.unskilled_trade
    return {trade: wage for trade, wage in wages.items()
            if trade == unskilled or idle_and_offered.get(trade, (0.0, 0.0))[1] > idle_and_offered.get(trade, (0.0, 0.0))[0]}


def interest_rate(economy):
    """The economy's own currency's rate from last year's memory, or None when it has none."""
    return economy.record.memory.rates.get(economy.setup.currency_id)


def credit_room(economy, borrower_id):
    """What lenders will still advance `borrower_id`. A borrower whose credit line was in the last clearing
    (credit_lines.py) has what the clearing granted it; any other, the share of the savings on offer that
    lenders put out less what the other borrowers took. None before lenders have met (no savings were
    offered yet)."""
    record = economy.record
    if record.funds_offered <= 0.0:
        return None
    if borrower_id in record.credit_granted:
        return record.credit_granted[borrower_id]
    others = sum(lent for borrower, lent in record.lent_by_borrower.items() if borrower != borrower_id)
    return capital_market.headroom(capital_market.lendable_capacity(record.funds_offered), others)


def all_producers(economy):
    """Every producer in the economy, as a live view (cheap: no copy), in the record's order."""
    return economy.record.producers.values()


def carried_last_year(economy):
    """Tonnes the merchants carried last year, origin tile -> destination tile, as a sorted copy."""
    return {key: dict(row) for key, row in sorted(economy.record.carried.items())}


def producers_of(economy, country=None):
    """The producers by agent id: those working on `country`'s tiles (the home country's when the economy
    holds several and none is named)."""
    scope = country_figures.home_when_shared(economy, country)
    if scope is None:
        return dict(economy.record.producers)
    tiles = country_figures.country_tiles(economy, scope)
    return {producer_id: producer for producer_id, producer in economy.record.producers.items() if producer.tile in tiles}


def external_trade_net(economy):
    """Money paid in over the external edge: exports less imports."""
    return economy.record.book.edge_net(EDGE_EXTERNAL, economy.setup.currency_id)


def external_trade_volume(economy):
    """Money moved either way over the external edge: exports plus imports."""
    return economy.record.book.edge_volume(EDGE_EXTERNAL, economy.setup.currency_id)


def _ranked_cohorts(economy, country=None):
    """The home country's household cohorts, poorest per head first (ties by people, then id)."""
    scope = country_figures.home_when_shared(economy, country)
    tiles = country_figures.country_tiles(economy, scope)
    cohorts = [cohort for cohort in economy.record.cohorts.values() if cohort.people > 0.0 and cohort.tile in tiles]
    return sorted(cohorts, key=lambda cohort: (cohort.last_year_income / cohort.people, cohort.people, cohort.agent_id))


def cohort_incomes(economy, country=None):
    """(people, last year's money income) of every household cohort, poorest per head first: the economy's
    own answer to what its bodies of people earn. Of `country` (the home country when the economy holds several)."""
    return [(cohort.people, cohort.last_year_income) for cohort in _ranked_cohorts(economy, country)]


def cohort_land_rents(economy, tiles=None, country=None):
    """(people, rent received last year) of every household cohort in the order of `cohort_incomes`, in the
    economy's units: the rent paid on each tile (only those in `tiles` when given) goes to the tile's cohorts
    by what each owns (`land_rents.rent_received_by_cohort`)."""
    received = land_rents.rent_received_by_cohort(economy.setup, economy.record, tiles)
    return [(cohort.people, received.get(cohort.agent_id, 0.0)) for cohort in _ranked_cohorts(economy, country)]


def watch_tiles(economy, tiles):
    """Keep the markets' books of the areas holding these tiles, beside the port's and the capital's, from the next
    clearing: where the game's buyers and sellers act. `offered_units` and `price_response(tile=...)` answer on a tile
    whose book is kept; elsewhere they have no book to read."""
    economy.watched_tiles = tuple(sorted(set(tiles)))


def prices_at(economy, tile):
    """(price of each good on one tile, goods whose shown price is not a market's), in the economy's unit: what a
    buyer or seller there faces. The price of the market area that holds the tile where it cleared lately, else
    the price the game is shown. A good the economy has no market for is absent."""
    return tile_prices.prices_at(economy, tile)


def offered_units(economy, good, tile):
    """Units the sellers in the tile's market area for a good held at its last clearing; None when the area has no
    book for the good."""
    return tile_prices.offered_units(economy, good, tile)


def price_response(economy, good, landed_units, taken_units, tile=None):
    """Factor on a good's price once `landed_units` more are offered and `taken_units` more are bought, from the
    book its market last cleared (the economy's own demand and supply). With a `tile`, that tile's market area and
    its own price. Without one, the port's market and the national price, which weighs each market area by what it
    usually trades, so a move at the port shows in it by the port's share of that value. None when the market has
    no book or traded nothing, infinite when more is taken than the sellers hold."""
    if tile is not None:
        return tile_prices.price_response_at(economy, good, tile, landed_units, taken_units)
    area = market_curves.port_area(economy.area_map, economy.setup.port_tile, good)
    curve = economy.record.curves.get(market_key(good, area)) if area is not None else None
    if curve is None:
        return None
    memory = economy.record.memory
    factor = market_curves.price_response(curve, good, memory.prices.get(market_key(good, area)), landed_units, taken_units)
    if factor is None or not math.isfinite(factor):
        return factor
    return 1.0 + _port_share(economy, good, area) * (factor - 1.0)


def _port_share(economy, good, area):
    """The port area's share of a good's usual traded value, which weighs a move at the port into the national
    price. Kept per economy until its next year, when prices and weights change."""
    cache = economy.__dict__.setdefault("_port_shares", {})
    key = (economy.record.memory.prices is not None and id(economy.record.memory.prices), good, area)
    if key not in cache:
        memory = economy.record.memory
        weights = memory.volume_weights or economy.record.volumes
        total = 0.0
        port_value = 0.0
        port_key = market_key(good, area)
        for market, price in memory.prices.items():
            if market.split(_KEY_SEPARATOR, 1)[0] == good:
                value = price * weights.get(market, 0.0)
                total += value
                if market == port_key:
                    port_value = value
        cache[key] = port_value / total if total > 0.0 else 1.0
    return cache[key]


def account_balance(economy, agent_id):
    """An agent's money balance in the economy's currency."""
    return economy.record.book.balance(agent_id, economy.setup.currency_id)


def account_holdings(economy, agent_id):
    """An agent's holdings in the book, as the book reports them."""
    return economy.record.book.holdings(agent_id)


def economy_from_record(setup, saved):
    """An Economy resumed from a record exported by `export_record`."""
    return Economy(setup, EconomyRecord.from_record(saved))


def blank_economy(setup):
    """An Economy at its opening, before any year has run."""
    return Economy(setup)


def backing_marginal_cost(economy):
    """(what the last unit of the money's backing good the opening needs costs to make, the opening's price for it),
    in the economy's units; None for money with no good behind it or when nothing makes the good."""
    cost = opening_metal.marginal_cost(economy.setup, economy.record)
    price = economy.setup.opening_prices.get(economy.record.currency.backing_good)
    return None if cost is None or not price else (cost, price)


def admit_recipes(economy, source_setup):
    """Give the economy the recipes, goods and opening prices a fresh setup (built from the society's present
    techniques) has and it lacks; a good with no market before gets one. False when nothing was missing."""
    return late_recipes.admit_recipes(economy, source_setup)


def set_improvements(economy, improvements):
    """Give the economy's hauls the built ways `{edge_key: {"road": true}}`; False when nothing changed."""
    return economy.set_improvements(improvements)


def export_record(economy, skip_currencies=()):
    """The economy's record as plain data, for saving; `skip_currencies` leaves out money another owner keeps in the
    same book."""
    return economy.record.to_record(skip_currencies)


def economy_contracts(economy):
    """The contract registry: the economy's term loans and, once the actors' purses adopt it, their facilities."""
    return economy.record.contracts


def economy_book(economy):
    """The double-entry book the economy's agents keep their money and goods in."""
    return economy.record.book


def begin_spin_up(economy):
    """Opens the hidden spin-up years, in which households' spending rises as far as their wealth allows."""
    economy.record.settling = True


def finish_spin_up(economy):
    """Closes the hidden spin-up years: the price level is rebased to one (expectations of inflation are kept)
    and the clock returns to zero."""
    rebase_basket_price_level(economy.setup, economy.record)
    economy.record.settling = False
    economy.record.memory.year = 0


def money_year_figures(economy, outcome):
    """The year's coin sink and source from its money audit (`YearOutcome.money_audit`), in the economy's unit:
    "wear" (coin worn away, positive), "struck" (coin the mint paid out net of what it took back: struck less
    melted), "change" (the year's change in the money stock) and "metal_held" (the metal the mint holds)."""
    spec = economy.record.currency
    edges = outcome.money_audit.edge_net
    held = account_holdings(economy, EDGE_MINT)["goods"].get(spec.backing_good, {}) if spec.backing_good else {}
    return {"wear": -edges.get(EDGE_WEAR, {}).get(spec.currency_id, 0.0),
            "struck": edges.get(EDGE_MINT, {}).get(spec.currency_id, 0.0),
            "change": outcome.money_audit.supply_change.get(spec.currency_id, 0.0),
            "metal_held": sum(quantity for quantity in held.values() if quantity > 0.0)}


def spin_up_state(economy, outcome):
    """The year's real output, hours hired and idle, producers' inventories and unmet need; see spin_up_state.py."""
    return year_spin_up_state(economy.setup, economy.record, outcome)


def note_spin_up_result(economy, result):
    """Records how the hidden spin-up ended (`AgentEconomy.final_result`); it is saved with the opening."""
    economy.record.spin_up_result = dict(result)


def trim_workforce_to_expected_hours(economy):
    """Cuts each skilled trade to the hours employers plan to want; see workforce_settle."""
    workforce_settle.trim_to_expected_hours(economy.setup, economy.record, economy.view())


def shown_prices_of(economy, country=None):
    """(prices, stale goods) the game is shown for this economy; see `notional.shown_prices`. Over the market
    areas touching `country` (the home country's when the economy holds several)."""
    scope = country_figures.home_when_shared(economy, country)
    if scope is None:
        return shown_prices(economy.setup, economy.record)
    return shown_prices(economy.setup, economy.record, country_figures.prices(economy, scope))


def shown_price_kinds_of(economy, country=None):
    """What each shown price is, by good: PRICE_TRADED, a quote kind (QUOTE_*) or an estimate (`notional.KIND_*`).
    Same scope as `shown_prices_of`."""
    scope = country_figures.home_when_shared(economy, country)
    market = None if scope is None else country_figures.prices(economy, scope)
    return shown_prices_with_kinds(economy.setup, economy.record, market)[2]


def move_goods(economy, moves):
    """Applies goods moves to the economy's book."""
    economy.record.book.move_many(moves)


def post_transfers(economy, transfers):
    """Applies money transfers to the economy's book."""
    economy.record.book.transfer_many(transfers)


def indebted_tiles(economy):
    """Tiles where households owe term loans, sorted: those a state could relieve of debt."""
    return record_indebted_tiles(economy.record)


def title_holdings(economy, tiles):
    """(holder -> share by tile, tenancy rows by tile) for the tiles: what a state plans a land decree from."""
    return record_title_holdings(economy.record, tiles)


def fugitive_share_by_tile(economy):
    """{tile: share of the people who belonged to it that are away, having fled the state's take} (flight_year.py)."""
    from .setup import area_tile
    workforce = economy.record.workforce
    shares = {}
    for area, row in sorted(economy.record.fugitives.items()):
        present = sum(sum(bands) for bands in workforce.workers.get(area, {}).values())
        if row["people"] > 0.0:
            shares[area_tile(area)] = row["people"] / (present + row["people"])
    return shares


def money_revenue_forms(economy):
    """Names of the revenue forms paid in money, which a state may farm out."""
    return [form.name for form in economy.setup.tax_forms if not form.paid_in]


def settle_agent_takings(economy, agent_id, edge_id, tile_note="agent's takings"):
    """Sends an agent's money and every unsold holding back over an edge; returns the money sent."""
    book, money = economy.record.book, economy.setup.currency_id
    proceeds = book.balance(agent_id, money)
    if proceeds > 0.0:
        book.transfer(Transfer(agent_id, edge_id, money, proceeds, tile_note))
    returns = [GoodsMove(agent_id, edge_id, good, tile, quantity, "unsold concern output")
               for good, tiles in book.holdings(agent_id)["goods"].items()
               for tile, quantity in tiles.items() if quantity > 0.0]
    book.move_many(returns)
    return proceeds


def rename_agent(economy, old, new):
    """`old` becomes `new` throughout the economy's records: money, goods, debts and claims, titles and shares are
    added to what `new` already holds; no posting is made, so no total moves."""
    economy.record.rename_agent(old, new)
