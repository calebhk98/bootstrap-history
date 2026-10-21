"""The arithmetic of the opening herds: the head the producers keep and the scaling to the pasture that carries it."""


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
