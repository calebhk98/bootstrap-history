"""Agriculture's rules as plain functions of plain values: the weather cells and their draws, the seed of a year's
weather, the manure of the draught herd."""
import collections
import random

from sim.unit_conversions import CIVIL_DAYS_PER_YEAR

WeatherCell = collections.namedtuple("WeatherCell", ("cell_id", "lat", "lon", "weight"))


def cell_morton_code(lat_degrees, lon_degrees, bits=16):
    """A Z-order (Morton) code for a lat/lon point: sorting by it keeps geographically close cells close together, so a
    contiguous run of the sorted cells is a spatial neighbourhood. Not a distance."""
    lat_fraction = (lat_degrees + 90.0) / 180.0
    lon_fraction = (lon_degrees + 180.0) / 360.0
    scale = 1 << bits
    lat_int = min(scale - 1, max(0, int(lat_fraction * scale)))
    lon_int = min(scale - 1, max(0, int(lon_fraction * scale)))
    code = 0
    for bit_index in range(bits):
        code |= ((lat_int >> bit_index) & 1) << (2 * bit_index)
        code |= ((lon_int >> bit_index) & 1) << (2 * bit_index + 1)
    return code


def raw_cells(tile_rows):
    """One cell per held land tile, its raw arable km2 as the weight. `tile_rows` is [(tile id, lat, lon, land area km2,
    arable fraction)] in the order the tiles are held."""
    return [WeatherCell(cell_id=tile_id, lat=lat, lon=lon, weight=land_area_km2 * arable_fraction)
            for tile_id, lat, lon, land_area_km2, arable_fraction in tile_rows]


def cap_cells(cells, cap):
    """`cells` unchanged when there are `cap` or fewer; otherwise merged, along a Z-order curve over their position, into
    exactly `cap` contiguous runs. A merged cell sits at the arable-weighted centroid of its run and weighs the run's
    summed arable km2, so the pooled land is unchanged and only the spatial resolution drops."""
    cap = int(cap)
    if len(cells) <= cap:
        return cells
    ordered = sorted(cells, key=lambda cell: cell_morton_code(cell.lat, cell.lon))
    cell_count = len(ordered)
    merged = []
    start = 0
    for group_index in range(cap):
        group_size = cell_count // cap + (1 if group_index < cell_count % cap else 0)
        group = ordered[start:start + group_size]
        start += group_size
        total_weight = sum(cell.weight for cell in group)
        if total_weight > 0.0:
            lat = sum(cell.lat * cell.weight for cell in group) / total_weight
            lon = sum(cell.lon * cell.weight for cell in group) / total_weight
        else:
            lat = sum(cell.lat for cell in group) / len(group)
            lon = sum(cell.lon for cell in group) / len(group)
        merged.append(WeatherCell(cell_id="pooled_%04d" % group_index, lat=lat, lon=lon, weight=total_weight))
    return merged


def pooled_cells(cells, cap):
    """The cells the harvest weather is pooled over: capped, then weighted by share of the arable land (equal shares when
    none has any). No cells give an empty list, which means one civilisation-wide draw."""
    if not cells:
        return []
    cells = cap_cells(cells, cap)
    total_weight = sum(cell.weight for cell in cells)
    if total_weight > 0.0:
        return [cell._replace(weight=cell.weight / total_weight) for cell in cells]
    equal_weight = 1.0 / len(cells)
    return [cell._replace(weight=equal_weight) for cell in cells]


def weather_seed(civilisation_id, region, year, salt):
    """A seed for one year's weather draw: a pure function of the civilisation, an optional region (a cell id), the year
    and the game's salt. The multipliers are arbitrary mixing constants that keep nearby years, regions and ids apart."""
    civ_component = sum((index + 1) * ord(character) for index, character in enumerate(str(civilisation_id)))
    region_component = 0 if region is None else sum((index + 1) * ord(character) for index, character in enumerate(str(region)))
    return (civ_component * 1000003 + region_component * 7919 + int(year) * 97 + salt * 104729) % (2 ** 32)


def independent_draws(cells, seed_of_cell):
    """One standard-normal draw per cell, each from its own generator seeded by `seed_of_cell(cell id)`."""
    return [random.Random(seed_of_cell(cell.cell_id)).gauss(0.0, 1.0) for cell in cells]


def draught_manure_kg(draught_herd_units, row):
    """Dung and urine a year the draught herd's recipes collect, kg, from the species row's rates."""
    return (draught_herd_units * row["manure_share_of_live_weight_per_day"]
            * CIVIL_DAYS_PER_YEAR * row["manure_collected_share"])



def purchase_refusal(hectares, cost, balance):
    """The cause a farmland purchase is refused for, or None: `not_positive` for no area, `cannot_afford` past the purse."""
    if hectares <= 0:
        return "not_positive"
    if cost > balance:
        return "cannot_afford"
    return None


def sale_refusal(hectares, owned):
    """The cause a farmland sale is refused for, or None: `not_positive` for no area, `not_owned` past the holding."""
    if hectares <= 0.0:
        return "not_positive"
    if hectares > owned + 1e-9:
        return "not_owned"
    return None
