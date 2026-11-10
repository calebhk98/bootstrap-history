"""The one wage rule (`trade_wages.priced_trade_wage`) over a block of trades and labour areas, read from the memory's labour table."""
import numpy

from sim.jit import njit


@njit
def labour_market_matrix(first, area, count, trade_count, area_count):
    """Per (trade number, area number): the labour market row of the pair, -1 where the memory has no such market. `first` and
    `area` are the labour table's columns, `count` its rows in use."""
    matrix = numpy.full((trade_count, area_count), -1, dtype=numpy.int64)
    for row in range(count):
        matrix[first[row], area[row]] = row
    return matrix


@njit
def market_rows_of(matrix, trade_numbers, area_numbers):
    """Per (trade, area) asked for: the labour market row, -1 where the trade or the area has no number (-1) or the pair no market."""
    rows = numpy.full((len(trade_numbers), len(area_numbers)), -1, dtype=numpy.int64)
    for trade in range(len(trade_numbers)):
        for area in range(len(area_numbers)):
            if trade_numbers[trade] >= 0 and area_numbers[area] >= 0:
                rows[trade, area] = matrix[trade_numbers[trade], area_numbers[area]]
    return rows


@njit
def wage_in_row(wages, row):
    """The remembered wage of a labour market row, NaN for no market (row -1) or a market holding none."""
    return numpy.nan if row < 0 else wages[row]


@njit
def wage_rule_grid(rows, wages, unskilled_rows, held_anywhere, opening_wages, premiums, level, unskilled_default):
    """`trade_wages.priced_trade_wage` for each (trade, area) of `rows` (labour market rows, -1 for none): what the market paid; else, for
    a trade the memory holds a wage for in no area, its opening wage times `level` (NaN: the setup gave none); else the area's unskilled
    wage (`unskilled_rows[area]`, or `unskilled_default` where the area paid none) times one plus the trade's `premiums`. NaN in the
    answer means the rule had nothing to price from (`unskilled_default` NaN): the caller takes the per-cell rule, which refuses."""
    grid = numpy.empty(rows.shape)
    for trade in range(rows.shape[0]):
        for area in range(rows.shape[1]):
            paid = wage_in_row(wages, rows[trade, area])
            if not numpy.isnan(paid):
                grid[trade, area] = paid
            elif not numpy.isnan(opening_wages[trade]) and not held_anywhere[trade]:
                grid[trade, area] = opening_wages[trade] * level
            else:
                unskilled = wage_in_row(wages, unskilled_rows[area])
                grid[trade, area] = (unskilled_default if numpy.isnan(unskilled) else unskilled) * (1.0 + premiums[trade])
    return grid
