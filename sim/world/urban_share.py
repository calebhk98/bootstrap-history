"""How many people a region's town can feed: the farms' surplus, and the surplus carried in.

A town lives on the food its region's farm households grow beyond their own need, and on what it can draw from
other regions' farms: a tonne carried costs labour-hours (`geography.route_costs`: land, river and sea alike), and
only the part of the tonne's own labour value left after carriage is delivered. A region's surplus is shared among
the towns that can reach it in proportion to what each would receive. Standalone: plain numbers in, people out.
"""
from typing import Dict, Mapping, Optional


def farm_surplus_people(farm_workers: float, kcal_per_farm_worker: float, people_per_farm_worker: float,
                        kcal_per_person: float) -> float:
    """People the farm workers' food feeds beyond their own households: what they grow, less the need of the
    people (workers and dependents) who live on it."""
    if kcal_per_person <= 0.0:
        raise ValueError("a person needs food energy")
    grown = max(0.0, farm_workers) * max(0.0, kcal_per_farm_worker)
    own_need = max(0.0, farm_workers) * max(0.0, people_per_farm_worker) * kcal_per_person
    return max(0.0, grown - own_need) / kcal_per_person


def delivered_share(carriage_hours_per_tonne: Optional[float], tonne_value_hours: float) -> float:
    """Share of a tonne of grain that arrives once carriage has taken its labour: one less the carriage hours over
    the hours the tonne took to grow; nothing where no route joins (None) or carriage costs the tonne's worth."""
    if carriage_hours_per_tonne is None or tonne_value_hours <= 0.0:
        return 0.0
    return max(0.0, 1.0 - carriage_hours_per_tonne / tonne_value_hours)


def town_ceilings(surplus_people: Mapping[str, float], carriage_hours: Mapping[str, Mapping[str, float]],
                  tonne_value_hours: Mapping[str, float]) -> Dict[str, float]:
    """{region: people its town can feed}. `surplus_people[source]` is each region's surplus; `carriage_hours[source]`
    maps the regions it reaches to the hours a tonne takes to get there (a region absent is out of reach; a region's
    own town pays none); `tonne_value_hours[source]` is the hours a tonne of its grain took to grow. A source's
    surplus is split among the towns in proportion to the share of a tonne each would receive, and each town gets
    that part, less carriage."""
    towns = sorted(surplus_people)
    ceilings = {town: 0.0 for town in towns}
    for source in towns:
        surplus = surplus_people[source]
        if surplus <= 0.0:
            continue
        reached = carriage_hours.get(source, {})
        shares = {town: (1.0 if town == source else
                         delivered_share(reached.get(town), tonne_value_hours.get(source, 0.0)))
                  for town in towns}
        total = sum(shares.values())
        if total <= 0.0:
            continue
        for town, share in shares.items():
            ceilings[town] += surplus * share / total * share
    return ceilings


def opening_shares(people: Mapping[str, float], ceilings: Mapping[str, float], urban_fraction: float) -> Dict[str, float]:
    """{region: share of its people living in town} at the opening: the nation's typed urban people (an initial
    condition) shared among the regions by what each region's town can feed, no region over what its town can feed or
    over all its people. Regions share the typed total as far as their ceilings allow."""
    total = sum(people.values())
    wanted = max(0.0, urban_fraction) * total
    cap = {tile: min(max(0.0, ceilings.get(tile, 0.0)), max(0.0, tile_people)) for tile, tile_people in people.items()}
    placed = {tile: 0.0 for tile in people}
    for _ in range(len(people) + 1):
        room = {tile: cap[tile] - placed[tile] for tile in people if cap[tile] - placed[tile] > 1e-9}
        remaining = wanted - sum(placed.values())
        if remaining <= 1e-9 or not room:
            break
        weight = sum(cap[tile] for tile in room)
        for tile in sorted(room):
            placed[tile] += min(room[tile], remaining * cap[tile] / weight)
    return {tile: (placed[tile] / people[tile] if people[tile] > 0.0 else 0.0) for tile in sorted(people)}


def band_for(civilisation_id: str, bands: Mapping[str, object]) -> Optional[Dict[str, object]]:
    """The validation band of a civilisation from the `bands` table (data/world/urban_share_bands.json), or None where
    no source was found."""
    found = bands.get(civilisation_id)
    return dict(found) if isinstance(found, dict) else None


def within_band(share: float, band: Optional[Mapping[str, object]]) -> Optional[bool]:
    """Whether `share` lies in the band; None when there is no band."""
    if band is None:
        return None
    return float(band["low"]) <= share <= float(band["high"])
