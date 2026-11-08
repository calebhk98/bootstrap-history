"""The producers of one good's turn, in one kernel call each for what they make and what they offer.

`produce_turn` is `producers.production_lines` for every planned producer of the turn at once: the scarcest of the plan, the capacity, the
inputs held and the hours hired sets the runs (Leontief), a run short of its tool draws the next tool its basket names and then works
by hand (`tool_fallback.draws`), and the moves come out in the order `production_lines` gives them: the hard inputs sorted by good,
the tools drawn sorted by good, the outputs sorted by good. Stocks are read from the book's stock rows and hours from the ledger's
`hours_hired` pair rows, as `goods_production.stocks_of_cells` and `goods_production_reads.pair_amounts` read them.

`offer_pairs` is the first half of `year_goods._quick_outputs` for every producer of the turn: for each output a producer holds beyond
the units its own runs use, the units, the price it expects (NaN: none, and the producer is `slow`, left to `producers.offers`) and the
good's spoilage; the reservations come from `year_goods_offers.offer_reservations`."""
import numpy

from sim.book_index import EMPTY, index_find, pack_key
from sim.jit import njit

KERNEL = {"error_model": "numpy"}
NEGLIGIBLE_REMAINING_SHARE = 1e-12        # `tool_fallback.draws`' remaining-runs threshold, as a share of the runs


@njit(**KERNEL)
def _stock(stock_key, stock_quantity, stock_index, agent, good, tile):
    """The quantity held in an (agent, good, tile) cell: zero where nothing was ever held or a number is -1."""
    if agent >= 0 and good >= 0 and tile >= 0:
        slot = index_find(stock_key, stock_index, pack_key(agent, good, tile))
        if slot >= 0:
            return stock_quantity[slot]
    return 0.0


@njit(**KERNEL)
def _hired(pair_key, pair_amount, pair_index, agent, trade):
    """The hours hired of a trade by an agent: zero where the ledger has no row or a number is -1."""
    if agent >= 0 and trade >= 0:
        position = index_find(pair_key, pair_index, pack_key(agent, trade, 0))
        if position != EMPTY:
            return 0.0 + pair_amount[position]
    return 0.0


@njit(**KERNEL)
def _draws(first, last_wear, wear_draw, wear_per_run, step_ptr, step_draw, step_units, step_factor, step_trade_ptr, step_trade_slot,
           held, labour_hours, runs, used, extra, order):
    """`tool_fallback.draws` for one producer: `used` (by draw good) and `extra` (hours by labour slot) are filled, and `order` lists
    the labour slots in the order their first extra hours were added; returns how many are listed."""
    used[:] = 0.0
    extra[:] = 0.0
    listed = 0
    threshold = NEGLIGIBLE_REMAINING_SHARE * max(1.0, runs)
    for wear in range(first, last_wear):
        draw = wear_draw[wear]
        per_run = wear_per_run[wear]
        first_runs = min(runs, held[draw] / per_run) if per_run > 0.0 else runs
        if first_runs > 0.0:
            used[draw] = used[draw] + first_runs * per_run
        remaining = runs - first_runs
        for step in range(step_ptr[wear], step_ptr[wear + 1]):
            if remaining <= threshold:
                break
            good = step_draw[step]
            if good >= 0 and step_units[step] > 0.0:
                covered = min(remaining, max(0.0, held[good] - used[good]) / step_units[step])
                if covered > 0.0:
                    used[good] = used[good] + covered * step_units[step]
            elif good >= 0:
                continue
            else:
                covered = remaining
            if covered > 0.0 and step_factor[step] > 1.0:
                for place in range(step_trade_ptr[step], step_trade_ptr[step + 1]):
                    slot = step_trade_slot[place]
                    if extra[slot] == 0.0 and not _listed(order, listed, slot):
                        order[listed] = slot
                        listed += 1
                    extra[slot] = extra[slot] + covered * (step_factor[step] - 1.0) * labour_hours[slot]
            remaining -= max(0.0, covered)
    return listed


@njit(**KERNEL)
def _listed(order, listed, slot):
    for place in range(listed):
        if order[place] == slot:
            return True
    return False


@njit(**KERNEL)
def produce_turn(runs_planned, agent, tile, recipe, capacity, yield_factor, scale_row, hours_scale,
                 hard_ptr, hard_good, hard_per_run, wear_ptr, wear_draw, wear_per_run, step_ptr, step_draw, step_units, step_factor,
                 step_trade_ptr, step_trade_slot, draw_ptr, draw_good, draw_listed, labour_ptr, labour_trade, labour_hours,
                 output_ptr, output_good, output_per_run, lines_most, good_book, trade_ledger,
                 stock_key, stock_quantity, stock_index, pair_key, pair_amount, pair_index):
    """What each producer of the turn makes. Per producer i: `runs_planned[i]` (NaN or not above zero: it makes nothing), the book's
    numbers of its `agent` and `tile`, its `recipe` row, `capacity`, `yield_factor`, and its crew's hours multipliers
    `hours_scale[scale_row[i]]` by trade column (one for a crew at the floor, else the multiplier `practice.recipe_for` applies).
    Returns the moves as columns: the producer's place i, the good's row, the quantity, whether it is an output and not an input."""
    count = len(runs_planned)
    room = 0
    for place in range(count):
        room += lines_most[recipe[place]]
    line_producer = numpy.zeros(room, dtype=numpy.int64)
    line_good = numpy.zeros(room, dtype=numpy.int64)
    line_quantity = numpy.zeros(room)
    line_output = numpy.zeros(room, dtype=numpy.bool_)
    lines = 0
    for place in range(count):
        planned = runs_planned[place]
        if not planned > 0.0:
            continue
        row = recipe[place]
        limit = min(planned, capacity[place])
        wanted_hard = hard_ptr[row + 1] - hard_ptr[row]
        held_hard = numpy.zeros(wanted_hard)
        for slot in range(wanted_hard):
            entry = hard_ptr[row] + slot
            held_hard[slot] = _stock(stock_key, stock_quantity, stock_index, agent[place], good_book[hard_good[entry]], tile[place])
            limit = min(limit, held_hard[slot] / hard_per_run[entry])
        slots = labour_ptr[row + 1] - labour_ptr[row]
        hours = numpy.zeros(slots)
        hired = numpy.zeros(slots)
        for slot in range(slots):
            entry = labour_ptr[row] + slot
            hours[slot] = labour_hours[entry] * hours_scale[scale_row[place], labour_trade[entry]]
            hired[slot] = _hired(pair_key, pair_amount, pair_index, agent[place], trade_ledger[labour_trade[entry]])
            limit = min(limit, hired[slot] / hours[slot])
        limit = max(0.0, limit)
        if limit <= 0.0:
            continue
        draws_here = draw_ptr[row + 1] - draw_ptr[row]
        held = numpy.zeros(draws_here)
        for slot in range(draws_here):
            entry = draw_ptr[row] + slot
            if draw_listed[entry] == 1:
                held[slot] = _stock(stock_key, stock_quantity, stock_index, agent[place], good_book[draw_good[entry]], tile[place])
        used = numpy.zeros(draws_here)
        extra = numpy.zeros(slots)
        order = numpy.zeros(slots, dtype=numpy.int64)
        listed = _draws(wear_ptr[row], wear_ptr[row + 1], wear_draw, wear_per_run, step_ptr, step_draw,
                        step_units, step_factor, step_trade_ptr, step_trade_slot, held, hours, limit, used, extra, order)
        stretched_any = False
        for place_listed in range(listed):
            slot = order[place_listed]
            if numpy.isfinite(extra[slot]) and extra[slot] > 0.0:
                stretched_any = True
                stretched = hours[slot] * limit + extra[slot]
                if stretched > hired[slot]:
                    limit *= max(0.0, hired[slot] / stretched)
        if limit <= 0.0:
            continue
        if stretched_any:
            listed = _draws(wear_ptr[row], wear_ptr[row + 1], wear_draw, wear_per_run, step_ptr,
                            step_draw, step_units, step_factor, step_trade_ptr, step_trade_slot, held, hours, limit,
                            used, extra, order)
        for slot in range(wanted_hard):
            entry = hard_ptr[row] + slot
            line_producer[lines], line_good[lines], line_output[lines] = place, hard_good[entry], False
            line_quantity[lines] = min(limit * hard_per_run[entry], held_hard[slot])
            lines += 1
        for slot in range(draws_here):
            if used[slot] > 0.0:
                line_producer[lines], line_good[lines], line_output[lines] = place, draw_good[draw_ptr[row] + slot], False
                line_quantity[lines] = used[slot]
                lines += 1
        achieved = limit * yield_factor[place]
        for entry in range(output_ptr[row], output_ptr[row + 1]):
            if achieved * output_per_run[entry] > 0.0:
                line_producer[lines], line_good[lines], line_output[lines] = place, output_good[entry], True
                line_quantity[lines] = achieved * output_per_run[entry]
                lines += 1
    return line_producer[:lines], line_good[:lines], line_quantity[:lines], line_output[:lines]
