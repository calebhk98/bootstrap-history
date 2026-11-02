"""Merchants carry what they bought at the year's end, and what each one expects, wants and holds follows from it."""
from sim.geography.api import flow_ledger
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import carried_book, carriage_fleet_book, carriage_hours, carriage_wear, merchants, merchants_transit, route_dues
from .market_memory import market_key
from .year_goods import _held_stock
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
    index = carriage_hours.hired_index(ledger) if crew is not None else {}
    carriers = {}
    for cohort in record.cohorts.values():
        held = carriers.get(cohort.tile)
        if held is None or cohort.income_class < record.cohorts[held].income_class:
            carriers[cohort.tile] = cohort.agent_id
    carried: dict = {}
    carried_goods: dict = {}
    carrier_goods = carriage_wear.carrier_goods(setup)
    prices = carriage_wear.last_prices(setup, record.memory) if carrier_goods else {}
    dues = route_dues.owed_per_tonne(setup, carriage)
    wear = carriage_wear.Wear(setup, carriage, record.carriage.area_imbalance) if carriage_wear.wears(setup) else None
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
                                    lambda key: carriage_hours.last_wage(record.memory, key), area_map.area_of)
        done = merchants.dispatch(merchant, fills, carriage, setup.specs, money,
                                  record.book.balance(merchant.agent_id, money), _held_stock(record.book, merchant.agent_id),
                                  carrier_of=carriers.get, crew=hire,
                                  carrier_money=None if wear is None else (
                                      lambda source, destination, each=merchant: carriage_wear.money_per_tonne(
                                          prices, wear, source, destination)),
                                  margin_kept=wear is not None,
                                  fleet=carriage_fleet_book.limit_for(wear, own_capacity[merchant.agent_id], hired.get(merchant.agent_id, {}))
                                  if lives else None, dues=dues)
        record.book.post(done.transfers + done.dues, done.moves)
        ledger.note_postings(done.transfers, "wages")
        ledger.note_postings(done.dues)
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
    record.carriage.set_carried(carried, carried_goods)


def _price_on(record, area_map, good, tile):
    """The price the good's market area holding the tile last cleared at; None when it has no market there or
    none has cleared."""
    try:
        return record.memory.prices.get(market_key(good, area_map.area_of(good, tile)))
    except KeyError:
        return None
