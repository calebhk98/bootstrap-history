"""Merchants carry what they bought at the year's end, and what each one expects, wants and holds follows from it."""
from sim.geography.api import flow_ledger
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import carried_book, carriage_fleet_book, carriage_wear_batch, carriage_hours, carriage_wear, merchants, merchants_transit, route_dues
from .cohort_reads import poorest_by_tile, populated_tiles
from .market_memory import market_key
from .inventory import held_stock
from .national_prices import usual_volumes
from .merchants_dispatch_answer import Dispatched
from .merchants_dispatch_pack import MerchantYear, YearHauls, fit_fleet, pack, run, wear_needed
from .year_ledger import YearLedger


def dispatch_merchants(setup, record, carriage, ledger: YearLedger, area_map) -> None:
    """Merchants carry what they bought. The crew hours the shipments need were hired in the year's labour
    market (carriage_hours.bids) and limit what is carried; a merchant with no plan yet (it has not shipped)
    is not limited. A fee is paid in parts to those who supply them: the crew by the labour market, the carriers
    worn and the feed the animals eat by the merchant buying them in the goods market (carriage_wear), and
    what is left (the carriers' interest, their losses, the margin) stays with the merchant that owns the carriers,
    whose owner draws it as profit. Where the setup names no carriers the whole fee still goes to the poorest
    households of the tile the goods leave (Complaints/552)."""
    money = setup.currency_id
    crew = carriage_hours.crew_for(setup, record.carriage, carriage)
    carriers = poorest_by_tile(record.cohorts)
    carried: dict = {}
    carried_goods: dict = {}
    carrier_goods = carriage_wear.carrier_goods(setup)
    prices = carriage_wear.last_prices(setup, record.memory, usual_volumes(record)) if carrier_goods else {}
    dues = _kept(route_dues.owed_per_tonne(setup, carriage, record.memory.opening_wage_level(money)))
    money_per_tonne = _kept(lambda source, destination: carriage_wear.money_per_tonne(prices, wear, source, destination))
    wear = carriage_wear.Wear(setup, carriage, record.carriage.area_imbalance) if carriage_wear.wears(setup) else None
    ordered = sorted(record.merchants.values(), key=lambda each: each.agent_id)
    record.book.move_many([move for merchant in ordered for move in merchants_transit.advance(merchant, setup.specs)])    # hauls on the road for years reach the tile or spoil
    lives = carriage_fleet_book.fleet_lives(setup) if wear is not None else {}
    own_capacity, hired = {}, {}
    if lives:
        carriage_wear_batch.settle_all(record.book, sorted(record.merchants), carrier_goods, {})     # the carriers each bought go to its carrier account
        for merchant in ordered:
            own_capacity[merchant.agent_id] = carriage_fleet_book.own_capacity(record.book, merchant.agent_id, lives)
    entries = _entries(setup, record, ledger, area_map, crew, ordered)
    hauls = YearHauls(carriage, setup.specs, carriers.get, money, dues, None if wear is None else wear.units_per_tonne,
                      None if wear is None else money_per_tonne, {}, prices)
    packed = pack(entries, hauls, sorted(lives))
    if lives:     # a merchant carries no more than its fleet bears; idle fleets are hired out to those short of one
        needed = {entry.merchant.agent_id: found for entry, found in zip(entries, wear_needed(packed))}
        hired, hauls.lent = carriage_fleet_book.share_idle(own_capacity, needed)
        for entry in entries:
            entry.own, entry.hired = own_capacity[entry.merchant.agent_id], hired.get(entry.merchant.agent_id, {})
            entry.fleet = carriage_fleet_book.limit_for(wear, entry.own, entry.hired)
        fit_fleet(packed)
    answer = Dispatched(*run(packed))
    worn: dict = {}     # the carrier units each merchant's shipments wore, settled for all of them after the loop
    shipping = []
    postings, fees, dues_paid, rents, moves = [], [], [], [], []
    for row, entry in enumerate(entries):
        merchant = entry.merchant
        if not entry.dispatching:
            if crew is not None:
                merchant.carriage_hours_wanted = {}     # nothing shipped: no carriers to bid for next year
                merchant.carriage_money_wanted = {}
            if wear is not None:     # its fleet's wanted size stands: it may ship again
                merchant.carrier_wear = {}
                shipping.append(merchant.agent_id)
            continue
        done = answer.dispatch_of(row)
        postings.extend(done.transfers + done.dues)
        fees.extend(done.transfers)
        dues_paid.extend(done.dues)
        moves.extend(done.moves)
        if crew is not None:
            merchant.carriage_hours_wanted = done.crew_hours_wanted
            merchant.carriage_money_wanted = done.crew_money_wanted
        if wear is not None:
            merchant.carrier_wear = answer.worn_of(row)
            shipping.append(merchant.agent_id)
            worn[merchant.agent_id] = {good: units for good, units in merchant.carrier_wear.items() if good not in lives}
            if lives:
                merchant.carrier_fleet_wanted = {good: max(0.0, units - hired.get(merchant.agent_id, {}).get(good, 0.0))
                                                 for good, units in done.fleet_wanted.items()}
                rent = answer.rent_of(row)
                postings.extend(rent)
                rents.extend(rent)
    record.book.post(postings, moves)
    ledger.note_postings(fees, "wages")
    ledger.note_postings(dues_paid)
    ledger.note_postings(rents)
    for move in moves:
        tonnes = move.quantity * setup.specs[move.good].unit_mass_kg / KILOGRAMS_PER_TONNE
        flow_ledger.record_flow(carried, move.tile, move.receiver_tile, tonnes)
        price_at_origin = _price_on(record, area_map, move.good, move.tile)
        price_at_destination = _price_on(record, area_map, move.good, move.receiver_tile)
        carried_book.note_carried(carried_goods, move.good, move.tile, move.receiver_tile, move.quantity, tonnes,
                                  price_at_origin, price_at_destination)
        source = setup.country_of(move.tile)
        if source != setup.civ_id and setup.country_of(move.receiver_tile) == setup.civ_id:
            carried_book.note_crossing(ledger.carried_in, move.giver, source, move.quantity, price_at_origin, price_at_destination)
    if wear is not None:
        carriage_wear_batch.settle_all(record.book, shipping, carrier_goods, worn)
    record.carriage.set_carried(carried, carried_goods)


def _entries(setup, record, ledger, area_map, crew, ordered):
    """Each merchant's year as `MerchantYear` (purse, stock, the crew hired for it), in the order their purses move."""
    money = setup.currency_id
    index = ledger.hours_hired_by_market if crew is not None else {}
    populated = populated_tiles(record.cohorts)
    bought_by = {}
    for (employer, trade, area), (bought, _paid) in index.items():
        bought_by.setdefault(employer, {})[(trade, area)] = bought
    cash = record.book.balances_of([merchant.agent_id for merchant in ordered], money).tolist()
    entries = []
    for merchant, purse in zip(ordered, cash):
        held = held_stock(record.book, merchant.agent_id)
        if not ledger.buy_fills.get(merchant.agent_id, []) and not merchants.ships_held_stock(merchant, held):
            entries.append(MerchantYear(merchant, purse, held, False))
            continue
        hire = None
        if crew is not None:
            if carriage_hours.planned(merchant):
                ledger.crew_hours_bought[merchant.agent_id] = bought_by.get(merchant.agent_id, {})
            hours_hired, wages = ((carriage_hours.engaged(record, merchant, index)) if carriage_hours.planned(merchant)
                                  else (None, {}))
            hire = merchants.CrewHire(crew.hours_per_tonne, hours_hired, wages,
                                      _kept_by_key(lambda key, each=merchant: carriage_hours.crew_wage(setup, record, each, key, populated)),
                                      area_map.area_of)
        entries.append(MerchantYear(merchant, purse, held, True, hire))
    return entries


def _kept(function):
    """`function(source, destination)` answered once for each pair this year (its answers are shared, not changed by callers)."""
    answers: dict = {}

    def kept(source, destination):
        key = (source, destination)
        if key not in answers:
            answers[key] = function(source, destination)
        return answers[key]
    return kept


def _kept_by_key(function):
    """`function(key)` answered once for each key."""
    answers: dict = {}

    def kept(key):
        if key not in answers:
            answers[key] = function(key)
        return answers[key]
    return kept


def _price_on(record, area_map, good, tile):
    """The price the good's market area holding the tile last cleared at; None when it has no market there or
    none has cleared."""
    try:
        return record.memory.cleared_prices.get(market_key(good, area_map.area_of(good, tile)))
    except KeyError:
        return None
