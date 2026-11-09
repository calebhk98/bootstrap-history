"""Every merchant's haul loop of the year in one kernel (the rule of `merchants.dispatch`, whose figures it gives): what each route
carries to each destination, the carrier's fee and the dues, limited by the crew hired, the fleet and the purse.

`plan_merchant` sizes the merchant's shipments and `carry_merchant` carries what its crew, fleet and purse allow; the sums that
`dispatch` took with `math.fsum` are `exact_sum`. The postings that follow (the purse, wear, rents) are `merchants_dispatch_settle_kernel`."""
import numpy

from sim.jit import njit
from .year_ledger_note_kernels import exact_sum


@njit
def split_route(routes, legs, route, shares):
    """The units of the route's stock each leg takes, in `shares[first leg + n]` (`merchants_legs.split`): by weight, equally when no
    leg has weight."""
    first, count = routes.first_leg[route], routes.leg_count[route]
    quantity = routes.held[route]
    if count == 1:
        shares[first] = quantity
        return
    positives = numpy.empty(count)
    for place in range(count):
        positives[place] = max(0.0, legs.weight[first + place])
    total = exact_sum(positives, count)
    for place in range(count):
        if total <= 0.0:
            shares[first + place] = quantity / count
        else:
            shares[first + place] = quantity * (positives[place] / total)


@njit
def tonnes_within(spare, pairs, pair, in_fleet):
    """The tonnes a haul of the pair can carry on the `spare` wear (`carriage_fleet.tonnes_within`); infinity when no fleet carrier limits."""
    found = numpy.inf
    for place in range(pairs.wear_count[pair]):
        carrier, units = pairs.wear_carrier[pair, place], pairs.wear_units[pair, place]
        if in_fleet[carrier] and units > 0.0:
            limit = max(0.0, spare[carrier]) / units
            if limit < found:
                found = limit
    return found


@njit
def wear_down(spare, pairs, pair, in_fleet, tonnes):
    """The fleet carriers a haul of `tonnes` of the pair wears take the wear off `spare`."""
    for place in range(pairs.wear_count[pair]):
        carrier = pairs.wear_carrier[pair, place]
        if in_fleet[carrier]:
            spare[carrier] -= tonnes * pairs.wear_units[pair, place]


@njit
def crew_money_paid(pairs, merchants, row, pair, tonnes_per_unit, per_unit):
    """The wages already paid inside the fee on a unit: the hours hired at what they were paid, never above the fee; a key nothing was hired
    for has none."""
    count = pairs.crew_count[pair]
    paid = numpy.empty(count)
    used = 0
    for place in range(count):
        wage = merchants.paid_wage[row, pairs.crew_key[pair, place]]
        if not numpy.isnan(wage):
            paid[used] = pairs.crew_hours[pair, place] * tonnes_per_unit * wage
            used += 1
    return min(per_unit, exact_sum(paid, used))


@njit
def crew_pay(pairs, merchants, row, pair, tonnes_per_unit):
    """What the haul's crew hours a unit cost at the wage of their markets."""
    count = pairs.crew_count[pair]
    cost = numpy.empty(count)
    for place in range(count):
        cost[place] = pairs.crew_hours[pair, place] * tonnes_per_unit * merchants.market_wage[row, pairs.crew_key[pair, place]]
    return exact_sum(cost, count)


@njit
def crew_hours_total(pairs, pair, tonnes_per_unit):
    count = pairs.crew_count[pair]
    hours = numpy.empty(count)
    for place in range(count):
        hours[place] = pairs.crew_hours[pair, place] * tonnes_per_unit
    return exact_sum(hours, count)


@njit
def payout_per_unit(pairs, merchants, row, pair, tonnes_per_unit, per_unit, crew_money, dues_sum, has_crew, has_wear):
    """What a unit's fee pays the carrier: the fee less the crew's wages, the carriers worn and the dues; with the carriers owned
    (`has_wear`) only the crew pay for hours nobody was hired for."""
    supplied = 0.0
    if has_wear and not numpy.isnan(pairs.money[pair]):
        supplied = min(max(0.0, per_unit - crew_money), pairs.money[pair] * tonnes_per_unit)
    payout = max(0.0, per_unit - crew_money - supplied - dues_sum)
    if has_wear:
        unhired = 0.0
        if has_crew and not merchants.has_plan[row]:
            unhired = crew_pay(pairs, merchants, row, pair, tonnes_per_unit)
        payout = min(payout, unhired)
    return payout


@njit
def dues_unit_sum(pairs, pair, tonnes_per_unit):
    count = pairs.dues_count[pair]
    owed = numpy.empty(count)
    for place in range(count):
        owed[place] = pairs.dues_owed[pair, place] * tonnes_per_unit
    return exact_sum(owed, count)


@njit
def ask_crew(pairs, merchants, results, row, pair, tonnes_per_unit, per_unit, quantity, spread):
    """What the shipment asks of its crew keys: the hours (`hours_wanted`) and what they are worth, shared by the route's hours."""
    count = pairs.crew_count[pair]
    if count == 0:
        return
    hours_all = crew_hours_total(pairs, pair, tonnes_per_unit)
    gain = 0.0
    if numpy.isfinite(spread):
        gain = max(0.0, spread - max(0.0, per_unit - crew_pay(pairs, merchants, row, pair, tonnes_per_unit)))
    for place in range(count):
        key = pairs.crew_key[pair, place]
        hours = pairs.crew_hours[pair, place] * tonnes_per_unit
        results.hours_wanted[row, key] += quantity * hours
        results.hours_wanted_named[row, key] = 1
        if hours_all > 0.0:
            results.money_wanted[row, key] += quantity * gain * hours / hours_all
            results.money_wanted_named[row, key] = 1


@njit
def plan_merchant(row, pairs, routes, legs, merchants, results, shares, planned, outlay, payout, flags, in_fleet,
                  kilograms_per_tonne):
    """The merchant's shipments sized: each leg's units, what a unit costs it and pays the carrier, the units the fleet would carry if every
    route were carried at its size (`planned`), the crew hours it asks and the fleet it calls for. `flags` is (has_crew, has_wear, has_fleet)."""
    has_crew, has_wear, has_fleet = flags[0], flags[1], flags[2]
    spare = merchants.fleet_capacity[row].copy()
    first_route = merchants.first_route[row]
    for route in range(first_route, first_route + merchants.route_count[row]):
        split_route(routes, legs, route, shares)
        tonnes_per_unit = routes.unit_mass_kg[route] / kilograms_per_tonne
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            pair = legs.pair[leg]
            if pair < 0:
                continue
            quantity = shares[leg]
            per_unit = pairs.cost[pair] * tonnes_per_unit
            crew_money = 0.0
            if has_crew:
                crew_money = crew_money_paid(pairs, merchants, row, pair, tonnes_per_unit, per_unit)
            dues_sum = dues_unit_sum(pairs, pair, tonnes_per_unit)
            payout[leg] = payout_per_unit(pairs, merchants, row, pair, tonnes_per_unit, per_unit, crew_money, dues_sum, has_crew, has_wear)
            outlay[leg] = payout[leg] + dues_sum
            planned[leg] = quantity
            if has_fleet and tonnes_per_unit > 0.0:
                for place in range(pairs.wear_count[pair]):
                    carrier = pairs.wear_carrier[pair, place]
                    results.fleet_wanted[row, carrier] += quantity * tonnes_per_unit * pairs.wear_units[pair, place]
                    results.fleet_wanted_named[row, carrier] = 1
                planned[leg] = min(quantity, tonnes_within(spare, pairs, pair, in_fleet) / tonnes_per_unit)
                wear_down(spare, pairs, pair, in_fleet, planned[leg] * tonnes_per_unit)
            if has_crew:
                ask_crew(pairs, merchants, results, row, pair, tonnes_per_unit, per_unit, quantity, legs.spread[leg])


@njit
def crew_cuts(row, pairs, routes, legs, merchants, planned, key_count, kilograms_per_tonne):
    """The share of each crew key's hours that was hired, where it falls short of what the planned shipments need; 1 where it does not."""
    needed = numpy.zeros(key_count)
    named = numpy.zeros(key_count, numpy.bool_)
    first_route = merchants.first_route[row]
    for route in range(first_route, first_route + merchants.route_count[row]):
        tonnes_per_unit = routes.unit_mass_kg[route] / kilograms_per_tonne
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            pair = legs.pair[leg]
            if pair < 0:
                continue
            for place in range(pairs.crew_count[pair]):
                key = pairs.crew_key[pair, place]
                needed[key] += planned[leg] * (pairs.crew_hours[pair, place] * tonnes_per_unit)
                named[key] = True
    cuts = numpy.ones(key_count)
    for key in range(key_count):
        hired = merchants.hired_hours[row, key]
        if named[key] and needed[key] > hired:
            cuts[key] = max(0.0, hired) / needed[key]
    return cuts


@njit
def carry_merchant(row, pairs, routes, legs, merchants, results_legs, shares, outlay, payout, flags, in_fleet,
                   cuts, kilograms_per_tonne, purse_margin):
    """The merchant's shipments carried, in order, to what the crew hired, the fleet and the purse allow; fees and dues are paid out of
    the purse, dues first. Fills `results_legs.carried`, `.fee` and `.dues_paid` (the fees are cut to the purse by the caller)."""
    has_fleet = flags[2]
    cash = merchants.cash[row]
    remaining = max(0.0, cash)
    purse = max(0.0, cash) * (1.0 - purse_margin)
    spare = merchants.fleet_capacity[row].copy()
    first_route = merchants.first_route[row]
    for route in range(first_route, first_route + merchants.route_count[row]):
        tonnes_per_unit = routes.unit_mass_kg[route] / kilograms_per_tonne
        for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
            pair = legs.pair[leg]
            if pair < 0:
                continue
            carried = shares[leg]
            cut = 1.0
            for place in range(pairs.crew_count[pair]):
                cut = min(cut, cuts[pairs.crew_key[pair, place]])
            if cut < 1.0:
                carried = shares[leg] * cut
            if has_fleet and tonnes_per_unit > 0.0:
                carried = min(carried, tonnes_within(spare, pairs, pair, in_fleet) / tonnes_per_unit)
            if outlay[leg] > 0.0:
                carried = min(carried, remaining / outlay[leg])
                remaining -= carried * outlay[leg]
            if has_fleet:
                wear_down(spare, pairs, pair, in_fleet, carried * tonnes_per_unit)
            if carried <= 0.0:
                continue
            results_legs.carried[leg] = carried
            for place in range(pairs.dues_count[pair]):
                paid = max(0.0, min(carried * (pairs.dues_owed[pair, place] * tonnes_per_unit), purse))
                purse -= paid
                results_legs.dues_paid[leg, place] = paid
            fee = max(0.0, min(carried * payout[leg], purse))
            purse -= fee
            results_legs.fee[leg] = fee


@njit
def wear_needed_all(pairs, routes, legs, merchants, in_fleet, kilograms_per_tonne):
    """The wear a year each merchant's routes put on each fleet good if every route's stock were carried to every leg's destination
    (`carriage_fleet_book.wear_needed`): [merchant row, carrier good]."""
    needed = numpy.zeros((merchants.row_count[0], len(in_fleet)))
    shares = numpy.zeros(len(legs.pair))
    for row in range(merchants.row_count[0]):
        first_route = merchants.first_route[row]
        for route in range(first_route, first_route + merchants.route_count[row]):
            split_route(routes, legs, route, shares)
            for leg in range(routes.first_leg[route], routes.first_leg[route] + routes.leg_count[route]):
                pair = legs.pair[leg]
                if pair < 0 or shares[leg] <= 0.0:
                    continue
                tonnes = shares[leg] * routes.unit_mass_kg[route] / kilograms_per_tonne
                for place in range(pairs.wear_count[pair]):
                    carrier = pairs.wear_carrier[pair, place]
                    if in_fleet[carrier]:
                        needed[row, carrier] += tonnes * pairs.wear_units[pair, place]
    return needed
