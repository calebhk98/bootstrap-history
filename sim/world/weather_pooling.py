"""Growing-season weather correlated by distance: the Cholesky factor of the cell-to-cell correlation and the pooled
harvest multiplier drawn through it. Plain arithmetic over cells (anything with `lat`, `lon`, `weight`); reads no
simulation."""
import math

EARTH_RADIUS_KM = 6371.0
# the factor's diagonal pivots are floored here so a matrix that is positive semi-definite only up to rounding still factorises
PIVOT_FLOOR = 1e-12


def chordal_position_km(lat_degrees, lon_degrees):
    """(x, y, z) kilometres on a sphere of Earth's radius. Straight-line distance between two of these keeps the
    exponential kernel positive semi-definite, which great-circle distance does not."""
    lat_radians = math.radians(lat_degrees)
    lon_radians = math.radians(lon_degrees)
    return (EARTH_RADIUS_KM * math.cos(lat_radians) * math.cos(lon_radians),
            EARTH_RADIUS_KM * math.cos(lat_radians) * math.sin(lon_radians),
            EARTH_RADIUS_KM * math.sin(lat_radians))


def correlation_cholesky(cells, decorrelation_length_km):
    """Lower-triangular factor of the matrix whose entry for two cells is exp(-chordal distance / decorrelation length)."""
    cell_count = len(cells)
    correlation = [[0.0] * cell_count for _ in range(cell_count)]
    positions_km = [chordal_position_km(cell.lat, cell.lon) for cell in cells]
    for row in range(cell_count):
        correlation[row][row] = 1.0
        row_x, row_y, row_z = positions_km[row]
        for col in range(row):
            col_x, col_y, col_z = positions_km[col]
            distance_km = math.sqrt((row_x - col_x) ** 2 + (row_y - col_y) ** 2 + (row_z - col_z) ** 2)
            value = math.exp(-distance_km / decorrelation_length_km)
            correlation[row][col] = value
            correlation[col][row] = value
    lower = [[0.0] * cell_count for _ in range(cell_count)]
    for row in range(cell_count):
        for col in range(row + 1):
            total = sum(lower[row][inner_index] * lower[col][inner_index] for inner_index in range(col))
            if row == col:
                lower[row][col] = math.sqrt(max(correlation[row][row] - total, PIVOT_FLOOR))
            else:
                lower[row][col] = (correlation[row][col] - total) / lower[col][col]
    return lower


def pooled_multiplier(cells, cholesky_lower, independent_draws, stdev, floor, ceiling):
    """The weight-averaged harvest multiplier: each cell's standard-normal draw is correlated through the factor,
    scaled to 1 + stdev * z, and clipped to [floor, ceiling] before the cells are averaged by weight."""
    pooled = 0.0
    for row, cell in enumerate(cells):
        correlated_z = sum(cholesky_lower[row][col] * independent_draws[col] for col in range(row + 1))
        pooled += cell.weight * max(floor, min(ceiling, 1.0 + stdev * correlated_z))
    return pooled


def tile_shares(cells):
    """{cell id: share of the total weight}; equal shares when no cell has weight, empty for no cells."""
    total = sum(cell.weight for cell in cells)
    if not cells:
        return {}
    if total > 0.0:
        return {cell.cell_id: cell.weight / total for cell in cells}
    return {cell.cell_id: 1.0 / len(cells) for cell in cells}


def harm_multiplier(share_by_tile, yield_factor_by_tile):
    """The share of the harvest left after harm: each tile with a factor loses (1 - factor) of its share of the arable
    land; a tile not named, or named by no share, loses nothing. 1.0 when nothing is harmed."""
    lost = 0.0
    for tile, factor in yield_factor_by_tile.items():
        lost += share_by_tile.get(tile, 0.0) * (1.0 - min(1.0, max(0.0, factor)))
    return max(0.0, 1.0 - lost)
