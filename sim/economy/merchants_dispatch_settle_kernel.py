"""What a merchant's dispatch does to its purse and fleet once its shipments are carried (`merchants_dispatch_kernel`), and the loop over
every merchant: the fees cut to the purse, the carriers its shipments wore, the rent it owes the merchants whose idle fleet it used.

The purses are the book's balances as they stand when the loop starts; each posting moves them in the order the caller posts them, so a
merchant paid rent by an earlier one dispatches with that money (as it did when each merchant was posted before the next was sized)."""
import numpy

from sim.jit import njit
from .merchants_dispatch_kernel import carry_merchant, crew_cuts, plan_merchant
from .year_ledger_note_kernels import exact_sum


@njit
def cut_fees_to_purse(row, routes, legs, merchants, results_legs, purse_margin):
    """The fees as posted against the merchant's purse (`merchants.within_purse`): all of them when their sum fits it, else each cut by the
    same share so the sum does."""
    first_route = merchants.first_route[row]
    fees = numpy.empty(len(legs.pair))
    count = 0
    for route in range(first_route, first_route + merchants.route_count[row]):
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            if results_legs.fee[leg] > 0.0:
                fees[count] = results_legs.fee[leg]
                count += 1
    total = exact_sum(fees, count)
    allowed = max(0.0, merchants.cash[row]) * (1.0 - purse_margin)
    if total <= allowed:
        return
    share = allowed / total
    for route in range(first_route, first_route + merchants.route_count[row]):
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            if results_legs.fee[leg] > 0.0:
                results_legs.fee[leg] = results_legs.fee[leg] * share


@njit
def pay_postings(row, pairs, routes, legs, merchants, results_legs):
    """The purse after the fees, then the dues, are paid out of it."""
    first_route = merchants.first_route[row]
    for route in range(first_route, first_route + merchants.route_count[row]):
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            if results_legs.fee[leg] > 0.0:
                merchants.cash[row] -= results_legs.fee[leg]
    for route in range(first_route, first_route + merchants.route_count[row]):
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            if legs.pair[leg] < 0:
                continue
            for place in range(pairs.dues_count[legs.pair[leg]]):
                if results_legs.dues_paid[leg, place] > 0.0:
                    merchants.cash[row] -= results_legs.dues_paid[leg, place]


@njit
def wear_of_shipments(row, pairs, routes, legs, merchants, results_legs, results, kilograms_per_tonne):
    """The carrier units the merchant's carried shipments wore (`carriage_wear.exposure`), by carrier good."""
    first_route = merchants.first_route[row]
    for route in range(first_route, first_route + merchants.route_count[row]):
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            pair = legs.pair[leg]
            if pair < 0 or results_legs.carried[leg] <= 0.0:
                continue
            tonnes = results_legs.carried[leg] * routes.unit_mass_kg[route] / kilograms_per_tonne
            for place in range(pairs.wear_count[pair]):
                carrier = pairs.wear_carrier[pair, place]
                results.worn[row, carrier] += tonnes * pairs.wear_units[pair, place]
                results.worn_named[row, carrier] = 1


@njit
def pay_rent(row, merchants, results, lent_share, lent_total, carrier_price):
    """What the merchant owes the merchants it hired carriers from (`carriage_fleet_book.rent_transfers`): the wear its shipments put beyond its own
    fleet, at most what it hired, at the carrier's price, shared by the wear each lent; never above its purse. Paid from it to them."""
    lessors = lent_share.shape[1]
    owed = numpy.zeros(lessors)
    for carrier in range(merchants.fleet_hired.shape[1]):
        if not merchants.fleet_hired_named[row, carrier]:
            continue
        beyond = min(merchants.fleet_hired[row, carrier], max(0.0, results.worn[row, carrier] - merchants.own_capacity[row, carrier]))
        if beyond <= 0.0 or lent_total[carrier] <= 0.0 or numpy.isnan(carrier_price[carrier]):
            continue
        for lessor in range(lessors):
            if lent_share[carrier, lessor] != 0.0:
                owed[lessor] += beyond * carrier_price[carrier] * lent_share[carrier, lessor] / lent_total[carrier]
    sum_owed = exact_sum(owed, lessors)
    scale = 0.0
    if sum_owed > 0.0:
        scale = min(1.0, max(0.0, merchants.cash[row]) / sum_owed)
    for lessor in range(lessors):
        money = owed[lessor] * scale
        if money > 0.0:
            results.rent[row, lessor] = money
            merchants.cash[row] -= money
            merchants.cash[lessor] += money


@njit
def dispatch_all(pairs, routes, legs, merchants, results_legs, results, flags, in_fleet, lent_share, lent_total, carrier_price,
                 kilograms_per_tonne, purse_margin):
    """Dispatch every merchant of the table that carries this year, in row order (the order the caller posts them in). `flags` is
    (crew is hired, carriers are owned and worn, a fleet bounds the carrying); `in_fleet[carrier]` marks the carrier goods held as a fleet;
    `lent_share[carrier, merchant]` is the wear that merchant lends of it, `lent_total` their sum and `carrier_price` its price (NaN: none)."""
    key_count = merchants.market_wage.shape[1]
    shares = numpy.zeros(len(legs.pair))
    planned = numpy.zeros(len(legs.pair))
    outlay = numpy.zeros(len(legs.pair))
    payout = numpy.zeros(len(legs.pair))
    for row in range(merchants.row_count[0]):
        if not merchants.dispatching[row]:
            continue
        plan_merchant(row, pairs, routes, legs, merchants, results, shares, planned, outlay, payout, flags, in_fleet, kilograms_per_tonne)
        cuts = numpy.ones(key_count)
        if flags[0] and merchants.has_plan[row]:
            cuts = crew_cuts(row, pairs, routes, legs, merchants, planned, key_count, kilograms_per_tonne)
        carry_merchant(row, pairs, routes, legs, merchants, results_legs, shares, outlay, payout, flags, in_fleet, cuts,
                       kilograms_per_tonne, purse_margin)
        cut_fees_to_purse(row, routes, legs, merchants, results_legs, purse_margin)
        pay_postings(row, pairs, routes, legs, merchants, results_legs)
        if flags[1]:
            wear_of_shipments(row, pairs, routes, legs, merchants, results_legs, results, kilograms_per_tonne)
        if flags[2]:
            pay_rent(row, merchants, results, lent_share, lent_total, carrier_price)
    for row in range(merchants.row_count[0]):
        results.cash_after[row] = merchants.cash[row]
