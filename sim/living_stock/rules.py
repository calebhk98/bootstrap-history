"""Living stock's rules as plain functions of the values they are given: gates, growth, opening herds, quotes, the draw."""
import hashlib

from sim.world import living_stock, stock_dynamics


def held_units(held_tonnes, tonnes_per_unit):
    """Units a stock of `held_tonnes` is, at `tonnes_per_unit` of the material."""
    return held_tonnes / tonnes_per_unit


def missing_stock(holds, held_tonnes_of, tonnes_per_unit_of):
    """[(material, units short)] of what a node's `holds` asks and is not held; [] for a node with no `holds`."""
    if not holds:
        return []
    return living_stock.unheld(held_tonnes_of, holds, tonnes_per_unit_of)


def stock_gates(holds, needs_first, node_id, held_units_of):
    """The living stock a node rests on, held beside needed, whichever way the data says it: its own `holds`, or a
    civilisation's `needs_first` gate on a material."""
    gates = [{"material": material, "needed": units, "held": round(held_units_of(material), 3), "brought_by": None}
             for material, units in sorted((holds or {}).items())]
    for key, entry in (needs_first or {}).items():
        if (not key.startswith("_") and isinstance(entry, dict) and entry.get("material")
                and node_id in (entry.get("ids") or ())):
            gates.append({"material": entry["material"], "needed": entry.get("units", 0.0),
                          "held": round(held_units_of(entry["material"]), 3), "brought_by": entry.get("node")})
    return gates


def needed_by(gates):
    """[{material, needed, held}] for the gates a node's own `holds` names, for rows that list nodes."""
    return [{"material": gate["material"], "needed": gate["needed"], "held": gate["held"]}
            for gate in gates if not gate["brought_by"]]


def held_herds(held_units_of, materials):
    """{material: units} of each of `materials` now held (rounded for the screens), those held only."""
    held = {material: round(held_units_of(material), 3) for material in sorted(materials)}
    return {material: units for material, units in held.items() if units > 0.0}


def pasture_room_kg(place, carried_kg, grazing_kg):
    """Live weight more that the place's grass keeps beside what already grazes there; None where the stock has no place."""
    if place is None:
        return None
    return max(0.0, carried_kg - grazing_kg)


def founder_billed_growth(grown, held, society_head):
    """The part of `grown` (units of increase on `held` units) that is the founder's to pay for: the society's own head
    (`society_head`, kept by its producers' recipes) is raised at their expense, only head beyond it is the founder's."""
    society = min(held, society_head)
    return grown * (held - society) / held


def growth_labour(entry, material, units):
    """{trade: hours} the labour of raising `units` more of the material, from its production entry."""
    if entry is None or units <= 0.0:
        return {}
    batches = units / entry["outputs"][material]
    return {trade: hours * batches for trade, hours in sorted((entry.get("labour_hours") or {}).items())}


def paid_share(cost, can_pay, balance):
    """The share of a growth's labour the purse could pay for (1 when all of it)."""
    if cost <= 0.0:
        return 1.0
    return 1.0 if can_pay else min(1.0, max(0.0, balance) / cost)


def material_year(held, rates, room, loss, society_head, paid_share_of):
    """(units after the year, units grown) of one held stock. Growth is held to `room`; the founder's part of it is
    billed, and `paid_share_of(billed units)` is the share of that the labour could be paid for."""
    grown = stock_dynamics.next_units(
        held, rates["natural_increase"], 0.0, rates["breeding_minimum_units"], room) - held
    if grown > 0.0:
        billed = founder_billed_growth(grown, held, society_head)
        grown -= billed * (1.0 - paid_share_of(billed))
    after = stock_dynamics.next_units(
        held, rates["natural_increase"], loss, rates["breeding_minimum_units"], grown)
    return after, grown


def society_herd_after(society_head, held, after):
    """The society's own head after a year: its share of the held herd follows the herd's change."""
    return min(held, society_head) * after / held


def herd_units_kept(producer_capacities, production):
    """{stock material: units} the herd producers keep: each producer's runs a year times the stock one run holds.
    `producer_capacities` is [(recipe_id, capacity_runs)]; `production` maps a recipe id to its production entry."""
    kept = {}
    for recipe_id, capacity_runs in producer_capacities:
        for material, units in (production.get(recipe_id, {}).get("herd_stock") or {}).items():
            kept[material] = kept.get(material, 0.0) + capacity_runs * units
    return kept


def opening_herds(kept, carried_kg, kilograms_per_unit_of, keeping_share_of):
    """{stock material: units} the society holds at the opening: `kept` scaled down together when the pasture
    (`carried_kg`) cannot carry its weight, then by the share of each herd that disease at the place lets stand."""
    weight = sum(units * kilograms_per_unit_of(material) for material, units in kept.items())
    scale = min(1.0, carried_kg / weight) if weight > 0.0 else 1.0
    return {material: units * scale * keeping_share_of(material) for material, units in sorted(kept.items())}


def endemic_keeping(rates, loss):
    """0 to 1: the share of an opening herd that can be kept where it stands. Disease at the place takes a share of
    the herd every year, and the herd holds only if breeding outruns that loss."""
    return 1.0 if loss <= 0.0 else max(0.0, 1.0 - loss / rates["natural_increase"])


def partner_holding(started, taken):
    """Units of the material the partner held at its date, less what smugglers have since taken. TRANSITIONAL
    HEURISTIC: the partner's stock is not simulated, so what it can sell is what it started with, not what it still
    has; a partner's own ledger would replace this."""
    return max(0.0, float(started) - taken)


def smuggling_draw(parts):
    """A draw in 0..1 fixed by the attempt (`parts`: year, taker, partner, stock, size and the purse the carrying has
    just left), so a save and a load cannot change the outcome and a repeat is a new draw."""
    key = "|".join(str(part) for part in parts)
    return int(hashlib.sha256(key.encode()).hexdigest()[:13], 16) / float(16 ** 13)


def not_trading_reply(partner, trading):
    return {"ok": False, "cause": "partner_not_trading",
            "error": "%s is not trading with you this year; those that are: %s" % (partner, ", ".join(trading) or "none")}
