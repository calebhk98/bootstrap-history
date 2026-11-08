"""The close's dividends as posting rows: `shares.split_dividend` and `ownership.spread` for every producer that pays, in one kernel.

A producer's dividend goes first to the holders of its shares (each their part, purpose "dividend on shares"), and what is left
(above the epsilon) to its owner as a dividend; a dividend paid to an owner cohort is then shared among the cohorts of its tile by
ownership share, and stays one payment to the owner when no cohort of the tile has a positive amount. The rows come out in the
order the Python made its payments: producer by producer, holders in name order, then the tile's cohorts in id order.

Payees are participants (year_close_owners.py), not book numbers."""
import numpy

from sim.jit import njit
from sim.labour.market.exact_sums import python_sum

DIVIDEND, SHARE_DIVIDEND = 0, 1        # the kind of a row: the owner's dividend, or a part paid to a holder of shares


@njit
def _tile_size(tile, tile_start):
    return 0 if tile < 0 else tile_start[tile + 1] - tile_start[tile]


@njit
def _emit(rows, payees, amounts, kinds, used, row, payee, amount, kind):
    rows[used] = row
    payees[used] = payee
    amounts[used] = amount
    kinds[used] = kind
    return used + 1


@njit
def _spread(rows, payees, amounts, kinds, used, row, amount, owner, tile, tile_start, member_participant, member_share, tile_total):
    """`ownership.spread` of one dividend to the owner `owner` whose tile is `tile` (-1: the owner is not a cohort)."""
    if tile >= 0 and tile_total[tile] > 0.0:
        before = used
        for member in range(tile_start[tile], tile_start[tile + 1]):
            part = amount * member_share[member] / tile_total[tile]
            if part > 0.0:
                used = _emit(rows, payees, amounts, kinds, used, row, member_participant[member], part, DIVIDEND)
        if used > before:
            return used
    return _emit(rows, payees, amounts, kinds, used, row, owner, amount, DIVIDEND)


@njit
def dividend_rows(pay_rows, dividend, has_shares, holder_start, holder_participant, holder_share, owner_participant, owner_tile,
                  tile_start, member_participant, member_share, tile_total, epsilon):
    """The posting rows (producer row, payee participant, amount, kind) for the producers in `pay_rows`, each paying
    `dividend[row]` (above zero). `owner_participant` and `owner_tile` are per producer row; the holder arrays are laid out by
    producer row (`ShareHolders`), the tile arrays by tile (`OwnerTable`)."""
    bound = 0
    widest = 0
    for position in range(len(pay_rows)):
        row = pay_rows[position]
        holders = holder_start[row + 1] - holder_start[row]
        bound += holders + max(1, _tile_size(owner_tile[row], tile_start)) + 1
        widest = max(widest, holders)
    rows = numpy.empty(bound, dtype=numpy.int64)
    payees = numpy.empty(bound, dtype=numpy.int64)
    amounts = numpy.empty(bound)
    kinds = numpy.empty(bound, dtype=numpy.int64)
    parts = numpy.empty(widest)
    used = 0
    for position in range(len(pay_rows)):
        row = pay_rows[position]
        amount = dividend[row]
        owner = owner_participant[row]
        tile = owner_tile[row]
        if has_shares[row] == 0:
            used = _spread(rows, payees, amounts, kinds, used, row, amount, owner, tile, tile_start, member_participant,
                           member_share, tile_total)
            continue
        first = holder_start[row]
        holders = holder_start[row + 1] - first
        for offset in range(holders):
            parts[offset] = amount * holder_share[first + offset]
            used = _emit(rows, payees, amounts, kinds, used, row, holder_participant[first + offset], parts[offset], SHARE_DIVIDEND)
        rest = amount - python_sum(parts, holders)
        if rest > epsilon:
            used = _spread(rows, payees, amounts, kinds, used, row, rest, owner, tile, tile_start, member_participant, member_share,
                           tile_total)
    return rows[:used].copy(), payees[:used].copy(), amounts[:used].copy(), kinds[:used].copy()


@njit
def add_in_order(participants, amounts, totals):
    """`totals[participant] += amount` for each row in order (the running sums a dictionary of incomes keeps)."""
    for position in range(len(participants)):
        totals[participants[position]] += amounts[position]
