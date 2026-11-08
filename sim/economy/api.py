"""The only door into sim/economy/: what code outside the package may import.

Outside code imports from here and reaches the simulation's economy through an `Economy` (built by
the markets module's port, sim/markets/port*.py), never through a submodule or a private name. The accessors below read the
record's internals so that callers do not hold `economy.record.<field>` in their own code.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the markets module's port hands it what it needs (sim/markets/port*.py)

import math

from . import route_dues, carried_book, carriage_wear, national_prices, crop_sites, unit_cost, country_figures, diagnostics, late_recipes, opening_metal, household_grinding, households, households_work, need_roles, labour_state, land_rents, market_curves, prices_at as tile_prices, taxes, tile_costs, workforce_settle
from .bank_founding import found_from_outside
from .diagnostics import person_equivalent_unemployment
from .fixture_setups import GRAIN as FIXTURE_STAPLE, LABOURER as FIXTURE_UNSKILLED_TRADE, small_setup as fixture_small_setup, stationary_setup as fixture_stationary_setup
from . import banks
from .banks import DEPOSIT_BANKING
from .funds import POOLED_FUNDS
from .insurance import INSURANCE_UNDERWRITING, RISK_POOLING
from .secondary_trade import BOND_MARKET, SHARE_TRADING
from .credit_lines import line_request as credit_line_request, actor_fundable as _actor_fundable, lender_standings as _lender_standings
from .credit import risk_premium
from .currency import currency_from_coin_standard
from .economy import Economy
from . import market_memory as market_memory_module
from .market_memory import KEY_SEPARATOR, market_key
from .market_table_specs import GOODS_MARKETS, GoodsMarkets      # the goods market table's spec and type (kernel_signatures declares its kernels from them)
from .opening_rate import opening_market_rate
from .year_ledger_store import LedgerTables      # the year ledger's tables (kernel_signatures declares its kernels from a fresh one)
from .metal_stock import COIN_WEAR_PER_YEAR
from .notional import costing_wages, shown_prices, shown_prices_with_kinds
from .producers import Producer, expected_output_prices, live_input_prices, live_wages
from .protocols import AgentOrders, EconomyYearInputs
from .recipes import recipes_from_production_data
from . import kept_wages, plant_builds, pool_deposits, quiet_year, trade_wages
from .tool_wear import with_tool_wear
from .record import EconomyRecord
from .setup import EconomySetup, SetupTrade, goods_specs, recipe_tile_key
from .setup import area_tile, labour_area, opening_price_today
from .state_wage_ceiling import WAGE_CEILING_MULTIPLE
from .types import (EDGE_CARGO, EDGE_CONSUMPTION, EDGE_EXCHANGE, EDGE_EXTERNAL, EDGE_LEGACY, EDGE_MINT, EDGE_PRODUCTION, EDGE_WEAR, Bid,
                    GoodsMove, LabourBid, LabourOffer, Offer, SiteLimit, Transfer, external_edge)
from .year_accounts import YearAccounts
from . import spin_up_sensitivity
from .unit_cost import variable_cost_per_run
from .titles_value import title_wealth
from .debt_relief import indebted_tiles as record_indebted_tiles
from .titles_moves import holdings as record_title_holdings
from .spin_up_state import spin_up_state as year_spin_up_state
from .year_close import rebase_basket_price_level
from .household_time_preference import HOUSEHOLD_TIME_PREFERENCE
from .trade_wages import premium_for_training_years, trade_premium
from sim.world import capital_market

__all__ = [
    "FIXTURE_STAPLE", "FIXTURE_UNSKILLED_TRADE", "fixture_small_setup", "fixture_stationary_setup",
    "YearAccounts", "spin_up_sensitivity",
    "carriage_wear", "crop_sites", "unit_cost", "diagnostics", "household_grinding", "households", "households_work", "need_roles", "taxes", "tile_costs", "currency_from_coin_standard", "Economy",
    "price_response", "prices_at", "offered_units", "watch_tiles",
    "shown_prices", "Producer", "expected_output_prices", "live_input_prices", "live_wages", "AgentOrders",
    "EconomyYearInputs", "recipe_tile_key", "recipes_from_production_data", "plant_builds", "with_tool_wear", "EconomyRecord", "EconomySetup", "SetupTrade", "SiteLimit",
    "goods_specs", "EDGE_EXTERNAL", "EDGE_LEGACY", "EDGE_CARGO", "EDGE_CONSUMPTION", "EDGE_PRODUCTION", "EDGE_EXCHANGE", "WAGE_CEILING_MULTIPLE", "external_edge", "Bid", "GoodsMove", "LabourBid", "LabourOffer", "Offer", "Transfer",
    "variable_cost_per_run", "rebase_basket_price_level", "trade_premium", "premium_for_training_years", "HOUSEHOLD_TIME_PREFERENCE", "title_wealth",
    "traded_volumes", "country_traded_volumes", "country_opening_basket", "market_record", "opening_quantities", "opening_prices_in_hours", "opening_price_in_current_money", "wages_by_trade_weighted", "interest_rate", "producers_of",
    "account_balance", "account_holdings",
    "credit_room", "credit_line_request", "economy_from_record", "blank_economy", "export_record", "economy_book", "bank_dividends_to", "economy_contracts", "finish_spin_up", "note_spin_up_result", "spin_up_state", "money_year_figures","shown_prices_of","shown_price_kinds_of",
    "settle_agent_takings", "route_dues_account", "tile_holders", "indebted_tiles", "fugitive_share_by_tile", "title_holdings", "money_revenue_forms", "admit_recipes", "move_goods", "post_transfers", "cohort_incomes", "cohort_land_rents", "land_rent_per_hectare",
    "land_rent_paid_by_tile", "land_rent_at_tile", "DEPOSIT_BANKING", "POOLED_FUNDS", "INSURANCE_UNDERWRITING", "RISK_POOLING", "BOND_MARKET", "SHARE_TRADING", "country_figures", "carried_book", "idle_hours_by_trade", "output_by_tile",
    "person_equivalent_unemployment", "labour_market_rows",
    "actor_fundable_amount", "risk_premium", "lender_listing", "note_pool_posting",
    "found_bank_from_outside", "people_by_trade", "people_by_tile_and_trade", "hours_paid_by_employer", "add_workers", "hours_offered_in_area_of",
    "all_producers", "carried_last_year", "backing_marginal_cost", "set_improvements", "begin_spin_up", "trim_workforce_to_expected_hours",
    "rename_agent", "coin_per_unit", "currency_id", "backing_good", "home_country", "economy_countries", "country_of_tile", "economy_tiles",
    "capital_tile", "port_tile", "tile_in_economy", "recipes_of", "good_specs", "recipe_allowed_at", "opening_prices_of", "unskilled_trade",
    "economy_trades", "opening_rate", "opening_market_rate", "labour_area", "COIN_WEAR_PER_YEAR", "working_hours_per_year", "opening_wage_level", "priced_trade_wage", "country_trade_wage",
    "trade_wage_at", "hunger_goods", "health_figures", "crop_site_inputs",
]


def found_bank_from_outside(economy, founder, capital_units, year, edge):
    """A bank founded by an actor whose money the engine keeps: `capital_units` come in over `edge` to its account and into
    the bank. The bank, or None when the capital is not positive."""
    return found_from_outside(economy.record, economy.setup.currency_id, founder, capital_units, year, edge)


def traded_volumes(economy):
    """Last year's traded quantity of each good, summed over its markets."""
    return country_figures.traded_volumes(economy, None)


def country_traded_volumes(economy, country=None):
    """Last year's traded quantity of each good over the markets of `country` (the home country when none is named)."""
    return country_figures.traded_volumes(economy, country or economy.setup.civ_id)


def country_opening_basket(economy, country=None):
    """Quantity of each good in the opening basket that falls to `country` (the home country when none is named)."""
    return country_figures.opening_basket(economy, country or economy.setup.civ_id)


def market_record(economy, good):
    """What the markets of one good did last year, summed over its areas, in the good's units: `sold` (traded),
    `unsold` (what sellers offered at the price their buyers faced beyond what was delivered) and `unmet` (what
    buyers asked for at the asks they faced beyond what was delivered), all after the year's second round of buying."""
    record = economy.record
    totals = {"sold": 0.0, "unsold": 0.0, "unmet": 0.0}
    for name, figures in (("sold", record.goods.volumes), ("unsold", record.goods.unsold), ("unmet", record.goods.unmet)):
        for key, quantity in figures.items():
            if key.split(KEY_SEPARATOR, 1)[0] == good:
                totals[name] += quantity
    return totals


def opening_quantities(economy):
    """Quantity of each good in the opening basket."""
    return dict(economy.record.goods.opening_basket)


def opening_prices_in_hours(economy):
    """Opening price of each good in hours of the unskilled trade's opening wage: the weights a basket is valued at."""
    wage = economy.setup.opening_wages[economy.setup.unskilled_trade]     # always there and positive: sim/markets/port_setup.py
    return {good: price / wage for good, price in sorted(economy.setup.opening_prices.items()) if price > 0.0}


def people_by_trade(economy, country=None):
    """Working people by trade across the labour areas of `country` (the home country when the economy holds
    several and none is named; every area when it holds one), as the labour core's state holds them."""
    scope = country_figures.home_when_shared(economy, country)
    if scope is None:
        return labour_state.people_by_trade_everywhere(economy.record.labour.workforce)
    return country_figures.people_by_trade(economy, scope)


def people_by_tile_and_trade(economy):
    """Working people of the labour core by tile and trade, over every labour area (trainees are not counted)."""
    return labour_state.PeopleByTile(economy.record.labour.workforce)


def land_rent_per_hectare(economy, country=None):
    """Mean rent per hectare-year producers paid last year over the tiles of `country` where land was let
    (the home country's when the economy holds several); None where none was let."""
    scope = country_figures.home_when_shared(economy, country)
    tiles = country_figures.country_tiles(economy, scope)
    rents = [rent for tile, rent in economy.record.land.land_rent.items() if rent > 0.0 and tile in tiles]
    return sum(rents) / len(rents) if rents else None


def land_rent_at_tile(economy, tile, country=None):
    """Rent per hectare-year the land market let land at on one tile last year; where none was let on this tile, the
    mean over the tiles of `country` (the home country's when none is named) where land was let; None where none was let
    anywhere."""
    rent = economy.record.land.land_rent.get(tile, 0.0)
    return rent if rent > 0.0 else land_rent_per_hectare(economy, country)


def output_by_tile(economy):
    """What the producers made last year, tile -> good -> units, as a sorted copy."""
    return {tile: dict(sorted(row.items())) for tile, row in sorted(economy.record.goods.output_by_tile.items())}


def land_rent_paid_by_tile(economy):
    """Rent producers paid on each tile where land was let last year, in the economy's units."""
    return land_rents.rent_paid_by_tile(economy.record)


def idle_hours_by_trade(economy, country=None):
    """(hours offered and not hired, hours offered) of each trade in the labour markets of `country` (the home
    country's when the economy holds several) in the last clearing: the jobs the labour core did not find."""
    return country_figures.idle_hours_by_trade(economy, country_figures.home_when_shared(economy, country))


def hours_paid_by_employer(economy, employer):
    """{trade: hours} the last labour clearing hired for `employer` (paid hours, bonded included); empty before one."""
    return dict(economy.record.labour.hours_paid_by_employer.get(employer, {}))


def add_workers(economy, tile, trade, people):
    """`people` more workers of `trade` in the labour core, on `tile`'s labour area: they are hired at the clearing like anyone.
    Worker-weighted wages and the figures kept between steps read the workforce, so the memory's write stamp moves."""
    economy.record.labour.add_workers(labour_area(tile), trade, people)
    market_memory_module.note_written()


def labour_market_rows(economy):
    """(people, hours offered, hours hired) of each (trade, area) labour market in the last clearing, in key order, for
    `person_equivalent_unemployment`. Offered is hired plus idle; the plot trade (people working their own land, most
    of the hours and people) is left out, so the unsold-hours share, which keeps it, is a different population."""
    record = economy.record
    plot = labour_state.plot_trade(economy.setup)
    rows = []
    for key in sorted(record.labour.hours_idle):
        trade, area = key.split(KEY_SEPARATOR, 1)
        if trade == plot:
            continue
        people = math.fsum(record.labour.workforce.workers.get(area, {}).get(trade, ()))
        hired = record.labour.hours_cleared_in(key)
        rows.append((people, hired + record.labour.hours_idle[key], hired))
    return rows


def hours_offered_in_area_of(economy, trade, tile):
    """Hours of `trade` the households of `tile`'s labour area offered at the last clearing (hired plus left idle, after
    the hours they keep for plot and home work); None before a clearing."""
    labour = economy.record.labour
    if not labour.hours_idle:
        return None
    key = market_key(trade, economy.view().area_of(trade, tile))
    return labour.hours_cleared_in(key) + labour.hours_idle.get(key, 0.0)


def wages_by_trade_weighted(economy, country=None):
    """The wage per hour of each trade the labour core holds a wage for, over `country`'s labour areas (the home
    country's when the economy holds several): `country_figures.wages_per_hour`, hours-hired weights, else people.
    A trade nobody hired is in it at the core's wage, not at an opening wage."""
    return country_figures.wages_per_hour(economy, country_figures.home_when_shared(economy, country))


def interest_rate(economy):
    """The economy's own currency's rate from last year's memory, or None when it has none."""
    return economy.record.memory.rates.get(economy.setup.currency_id)


def credit_room(economy, borrower_id):
    """What lenders will still advance `borrower_id`. A borrower whose credit line was in the last clearing
    (credit_lines.py) has what the clearing granted it; any other, the share of the savings on offer that
    lenders put out less what the other borrowers took. None only before lenders have met; lenders that met with no savings
    on offer leave no room, 0.0."""
    record = economy.record
    if not record.credit.lenders_met:
        return None
    if borrower_id in record.credit.credit_granted:
        return record.credit.credit_granted[borrower_id]
    others = sum(lent for borrower, lent in record.credit.lent_by_borrower.items() if borrower != borrower_id)
    return capital_market.headroom(capital_market.lendable_capacity(record.credit.funds_offered), others)


def all_producers(economy):
    """Every producer in the economy, as a live view (cheap: no copy), in the record's order."""
    return economy.record.producers.values()


def carried_last_year(economy):
    """Tonnes the merchants carried last year, origin tile -> destination tile, as a sorted copy."""
    return {key: dict(row) for key, row in sorted(economy.record.carriage.carried.items())}


def producers_of(economy, country=None):
    """The producers by agent id: those working on `country`'s tiles (the home country's when the economy
    holds several and none is named)."""
    scope = country_figures.home_when_shared(economy, country)
    if scope is None:
        return dict(economy.record.producers)
    tiles = country_figures.country_tiles(economy, scope)
    return {producer_id: producer for producer_id, producer in economy.record.producers.items() if producer.tile in tiles}


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
    received = land_rents.rent_received_by_cohort(economy.record, tiles)
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
    curve = economy.record.goods.curves.get(market_key(good, area)) if area is not None else None
    if curve is None:
        return None
    memory = economy.record.memory
    factor = market_curves.price_response(curve, good, memory.prices.get(market_key(good, area)), landed_units, taken_units)
    if factor is None or not math.isfinite(factor):
        return factor
    return 1.0 + national_prices.port_share(economy.record, good, market_key(good, area)) * (factor - 1.0)


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
    return economy.record.credit.contracts


def economy_book(economy):
    """The double-entry book the economy's agents keep their money and goods in."""
    return economy.record.book


def bank_dividends_to(economy, owner_id):
    """What the banks `owner_id` founded paid it as a dividend at the last year end, when it keeps its money outside the
    economy's households (a seat); zero for a household's dividend, which its tile's cohorts hold."""
    return banks.dividends_paid_to(economy.record, owner_id)


def begin_spin_up(economy):
    """Opens the hidden spin-up years, in which households' spending rises as far as their wealth allows."""
    economy.record.settling = True


def finish_spin_up(economy):
    """Closes the hidden spin-up years: the price level is rebased to one (expectations of inflation are kept)
    and the clock returns to zero. Route dues the hidden years collected pay no one: they return over the exchange edge."""
    for holder in tile_holders(economy):
        settle_agent_takings(economy, route_dues_account(holder), EDGE_EXCHANGE)
    rebase_basket_price_level(economy.setup, economy.record)
    economy.record.settling = False
    economy.record.memory.reset_year()


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


def settle_economy(economy):
    """Its step has returned: figures read from its record are kept until it next steps (`quiet_year`)."""
    quiet_year.settle(economy)


def shown_prices_of(economy, country=None):
    """(prices, stale goods) the game is shown for this economy; see `notional.shown_prices`. Over the market
    areas touching `country` (the home country's when the economy holds several)."""
    prices, stale, _kinds = _shown(economy, country)
    return dict(prices), set(stale)


def shown_price_kinds_of(economy, country=None):
    """What each shown price is, by good: PRICE_SMOOTHED_TRADE, a quote kind (QUOTE_*) or an estimate (`notional.KIND_*`).
    Same scope as `shown_prices_of`."""
    return dict(_shown(economy, country)[2])


def _shown(economy, country):
    """`notional.shown_prices_with_kinds` for the scope, worked out once while the economy stands between steps."""
    scope = country_figures.home_when_shared(economy, country)

    def compute():
        market = None if scope is None else country_figures.prices(economy, scope)
        wages = quiet_year.kept(economy, "costing_wages", lambda: costing_wages(economy.setup, economy.record))
        remembered = quiet_year.kept(economy, "price_kinds", economy.record.memory.price_kinds_by_good)
        return shown_prices_with_kinds(economy.setup, economy.record, market, wages, remembered)
    return quiet_year.kept(economy, ("shown", scope), compute)


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
    workforce = economy.record.labour.workforce
    shares = {}
    for area, row in sorted(economy.record.unfree.fugitives.items()):
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


# ---- What the markets port asks of the economy's setup (sim/markets/port*.py) ----
# Plain facts of the economy's setup, answered here so the port holds no `economy.setup.<field>`.

def coin_per_unit(economy):
    """Money (the game's coin) worth one economy unit."""
    return economy.setup.coin_per_unit


def currency_id(economy):
    return economy.setup.currency_id


def backing_good(economy):
    """The good that backs the money, or None for fiat money."""
    return economy.setup.currency.backing_good


def home_country(economy):
    return economy.setup.civ_id


def economy_countries(economy):
    """Every country with tiles in this economy (the home country among them)."""
    return economy.setup.countries()


def country_of_tile(economy, tile):
    return economy.setup.country_of(tile)


def route_dues_account(holder):
    """The account the route dues owed to a holder collect in (settle it with `settle_agent_takings`)."""
    return route_dues.account(holder)


def tile_holders(economy):
    """Every holder of tiles in the economy (the countries and seats their dues are paid to), sorted."""
    return sorted(economy.setup.countries())


def economy_tiles(economy):
    return economy.setup.tiles


def capital_tile(economy):
    return economy.setup.capital_tile


def port_tile(economy):
    return economy.setup.port_tile


def tile_in_economy(economy, tile):
    """`tile` when the economy has it, else its capital tile."""
    return tile if tile in economy.setup.tiles else economy.setup.capital_tile


def recipes_of(economy):
    """{recipe id: recipe} the economy runs."""
    return economy.setup.recipes


def good_specs(economy):
    """{good: spec} of the goods the economy knows."""
    return economy.setup.specs


def recipe_allowed_at(economy, recipe_id, tile):
    return economy.setup.recipe_allowed(recipe_id, tile)


def opening_prices_of(economy):
    return economy.setup.opening_prices


def opening_price_in_current_money(economy, good):
    """The opening price of a good in today's money; None when the setup holds none."""
    return opening_price_today(economy.setup, economy.record.memory, good)


def unskilled_trade(economy):
    return economy.setup.unskilled_trade


def economy_trades(economy):
    """The trades the labour core has markets for."""
    return frozenset(economy.setup.trades)


def opening_rate(economy):
    return economy.setup.opening_rate


def working_hours_per_year(economy):
    return economy.setup.working_hours_per_year


def opening_wage_level(economy):
    """Today's money per opening-year money for the wages the setup opened with (`MarketMemory.opening_wage_level`)."""
    return economy.record.memory.opening_wage_level(economy.setup.currency_id)


def priced_trade_wage(economy, trade, paid, unskilled):
    """The wage per hour of a trade by the one rule (`trade_wages`), in the economy's units, for any scope: the caller
    names what that scope paid for the trade and for the unskilled trade (None where nothing)."""
    return trade_wages.priced_trade_wage(economy.setup, trade, paid, unskilled, opening_wage_level(economy),
                                         economy.record.memory.holds_wage_for(trade))


def country_trade_wage(economy, trade, country=None):
    """The wage per hour of a trade in a country (the home country's when none is named) by the one rule, on the
    wages its labour areas hold (`wages_by_trade_weighted`); the opening wage stands in only for a trade the core
    holds no wage for in any of them."""
    wages = wages_by_trade_weighted(economy, country)
    return priced_trade_wage(economy, trade, wages.get(trade), wages.get(economy.setup.unskilled_trade))


def trade_wage_at(economy, trade, tile):
    """The wage per hour a bid for `trade` on `tile` is funded at: the area's last wage, else the one wage rule
    (`trade_wages.wage_in_area`)."""
    memory = economy.record.memory

    def compute():
        return trade_wages.wage_in_area(economy.setup, memory, trade, economy.view().area_of(trade, tile))
    return kept_wages.kept(memory, ("trade_wage", trade, tile), compute)


def hunger_goods(economy):
    """The goods the hunger need's basket buys, or () when the basket has no such need."""
    setup = economy.setup
    need = next((spec for spec in setup.basket.needs if spec.need_id == setup.hunger_need), None)
    return () if need is None else tuple(good for good, _effect in need.goods)


def health_figures(economy, outcomes, staple, metals):
    """The health figures (sim/economy/diagnostics.py) over the yearly outcomes kept."""
    return diagnostics.summary(outcomes, economy.setup, staple, metals)


def crop_site_inputs(economy):
    """(yield factor by recipe and tile, land a run takes by recipe) for the producers that crop land."""
    return economy.setup.yield_factor_by_recipe_tile, economy.setup.land_per_run


def actor_fundable_amount(economy, amount, existing_debt, collateral_value, arrears):
    """The most of a draw of `amount` an actor that already owes `existing_debt` is lent, by the same rule as every borrower
    in the clearing (credit_lines.actor_fundable) at the lowest rate any lender asked at the last lending. Economy units.
    None only before lenders have met; lenders that met with no savings on offer fund nothing, 0.0."""
    credit = economy.record.credit
    if not credit.lenders_met:
        return None
    ask = credit.lowest_ask_offered
    if ask is None:
        return 0.0
    rate = interest_rate(economy)
    return _actor_fundable(amount, existing_debt, collateral_value, arrears, economy.setup.opening_rate if rate is None else rate, ask)


def lender_listing(economy):
    """{"currency", "coin_per_unit", "lenders"}: the lenders of the last lending, cheapest ask first, each with its kind
    (cohort, bank, fund), what it offered, what its account holds and its ask, in the economy's units."""
    currency = economy.setup.currency_id
    return {"currency": currency, "coin_per_unit": economy.setup.coin_per_unit,
            "lenders": _lender_standings(economy.record, currency)}


def note_pool_posting(economy, lender, units):
    """The actors' pool paid `lender` interest (positive) or took a default's loss from its deposit (negative), in the economy's unit."""
    pool_deposits.note_pool_posting(economy.record, lender, units)
